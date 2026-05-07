"""
simulator.py — Lambda handler + local CLI
Loads ipl_fixtures.py and fifa_fixtures.py from S3 as Python source,
or imports them directly when running locally.
"""

import argparse, random, json, os, io, sys
import joblib, numpy as np
from collections import defaultdict
from copy import deepcopy

IS_LAMBDA = bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

# ── Fixture loading ───────────────────────────────────────────────────────────
# Locally  : import directly
# In Lambda: load .py source from S3, exec into a namespace, pull constants out

def _load_py_from_s3(key):
    import boto3
    bucket = os.environ["MODEL_BUCKET"]
    src = boto3.client("s3").get_object(Bucket=bucket, Key=key)["Body"].read().decode()
    ns = {}
    exec(compile(src, key, "exec"), ns)
    return ns

if IS_LAMBDA:
    _fifa = _load_py_from_s3("fifa_fixtures.py")
    FIFA_GROUPS        = _fifa["FIFA_GROUPS"]
    FIFA_GROUP_FIXTURES= _fifa["FIFA_GROUP_FIXTURES"]
    resolve_team       = _fifa["resolve_team"]

    _ipl = _load_py_from_s3("ipl_fixtures.py")
    IPL_TEAMS              = _ipl["IPL_TEAMS"]
    IPL_POINTS_TABLE       = _ipl["IPL_POINTS_TABLE"]
    IPL_REMAINING_FIXTURES = _ipl["IPL_REMAINING_FIXTURES"]
else:
    sys.path.insert(0, os.path.dirname(__file__) or ".")
    try:
        from fifa_fixtures import FIFA_GROUPS, FIFA_GROUP_FIXTURES, resolve_team
        from ipl_fixtures  import IPL_TEAMS, IPL_POINTS_TABLE, IPL_REMAINING_FIXTURES
    except ImportError as e:
        raise ImportError(f"Run from the directory containing fifa_fixtures.py: {e}")

N_SIMULATIONS = 10_000

# ── Model cache ───────────────────────────────────────────────────────────────
_cache = {}

def _load(key):
    if key in _cache:
        return _cache[key]
    if IS_LAMBDA:
        import boto3
        bucket = os.environ["MODEL_BUCKET"]
        obj    = boto3.client("s3").get_object(Bucket=bucket, Key=key)
        _cache[key] = joblib.load(io.BytesIO(obj["Body"].read()))
    else:
        _cache[key] = joblib.load(key)
    return _cache[key]

def load_ipl():
    return _load("ipl_model.pkl"), _load("ipl_le_t1.pkl"), \
           _load("ipl_le_t2.pkl"), _load("ipl_le_venue.pkl")

def load_fifa():
    return _load("fifa_model.pkl"), _load("fifa_le_home.pkl"), _load("fifa_le_away.pkl")

# ── Encoders ──────────────────────────────────────────────────────────────────
def _enc(le, val, fallback=0):
    try:    return int(le.transform([val])[0])
    except: return fallback

# ── IPL features: 14 — matches train_ipl.py exactly ──────────────────────────
# t1_enc, t2_enc, toss_won_by_team1, toss_bat_first, venue_enc, stage_weight,
# t1_win_rate, t2_win_rate, t1_streak, t2_streak, wr_diff, streak_diff,
# h2h_t1_win_rate, season_num

IPL_STAGE_W = {"league":1,"qualifier_1":2,"eliminator":2,"qualifier_2":2,"final":3}

def ipl_feats(le_t1, le_t2, le_venue, t1, t2,
              venue=None, stage="league",
              t1_wr=0.5, t2_wr=0.5, t1_st=0, t2_st=0, h2h=0.5):
    return [
        _enc(le_t1, t1), _enc(le_t2, t2),   # 1-2
        1, 1,                                 # 3-4 toss defaults
        _enc(le_venue, venue) if venue else 0,# 5   venue_enc
        IPL_STAGE_W.get(stage, 1),            # 6   stage_weight
        t1_wr, t2_wr,                         # 7-8
        t1_st, t2_st,                         # 9-10
        t1_wr - t2_wr, t1_st - t2_st,        # 11-12 wr_diff, streak_diff
        h2h,                                  # 13
        2026,                                 # 14 season_num
    ]

def ipl_win_prob(model, le_t1, le_t2, le_venue,
                 t1, t2, venue=None, stage="league",
                 t1_wr=0.5, t2_wr=0.5):
    f  = ipl_feats(le_t1, le_t2, le_venue, t1, t2, venue, stage, t1_wr, t2_wr)
    pr = model.predict_proba([f])[0]
    cl = list(model.classes_)
    return float(pr[cl.index(1)])

# ── FIFA features: 11 — matches train_fifa.py exactly ────────────────────────
# home_enc, away_enc, tournament_weight, is_neutral,
# home_win_rate, away_win_rate, home_avg_gd, away_avg_gd,
# wr_diff, gd_diff, h2h_home_win_rate

FIFA_STAGE_W = {"group":5,"round_of_32":6,"round_of_16":7,
                "quarterfinal":8,"semifinal":9,"final":10}

def fifa_feats(le_home, le_away, home, away, stage="group",
               h_wr=0.45, a_wr=0.40):
    h = _enc(le_home, resolve_team(home))
    a = _enc(le_away, resolve_team(away))
    tw = FIFA_STAGE_W.get(stage, 5)
    return [h, a, tw, 0, h_wr, a_wr, 0.1, -0.1, h_wr-a_wr, 0.2, 0.45]

def fifa_wdl(model, le_home, le_away, home, away, stage="group"):
    pr = model.predict_proba([fifa_feats(le_home, le_away, home, away, stage)])[0]
    cl = list(model.classes_)
    p  = {c: float(v) for c, v in zip(cl, pr)}
    return p.get("win",0.33), p.get("draw",0.34), p.get("loss",0.33)

# ═══════════════════════════════════════════════════════════════════════════════
#  IPL SIMULATOR
# ═══════════════════════════════════════════════════════════════════════════════
def _parse_fixture(fix):
    """Accept tuple (t1,t2,venue) or dict {team1,team2,venue}."""
    if isinstance(fix, dict):
        return fix["team1"], fix["team2"], fix.get("venue")
    return fix[0], fix[1], fix[2] if len(fix) > 2 else None

def simulate_ipl_season(model, le_t1, le_t2, le_venue, points_table, fixtures):
    pts = deepcopy(points_table)

    # Ensure all IPL teams exist in pts
    for t in IPL_TEAMS:
        if t not in pts:
            pts[t] = {"played":0,"won":0,"lost":0,"nr":0,"pts":0,"nrr":0.0}

    for fix in fixtures:
        t1, t2, venue = _parse_fixture(fix)
        played1 = max(pts[t1].get("played", 1), 1)
        played2 = max(pts[t2].get("played", 1), 1)
        t1_wr = pts[t1].get("won", 0) / played1
        t2_wr = pts[t2].get("won", 0) / played2

        p = ipl_win_prob(model, le_t1, le_t2, le_venue,
                          t1, t2, venue, t1_wr=t1_wr, t2_wr=t2_wr)
        winner = t1 if random.random() < p else t2
        loser  = t2 if winner == t1 else t1

        pts[winner]["pts"]    += 2
        pts[winner]["won"]    = pts[winner].get("won", 0) + 1
        pts[winner]["played"] = pts[winner].get("played", 0) + 1
        pts[loser]["lost"]    = pts[loser].get("lost", 0) + 1
        pts[loser]["played"]  = pts[loser].get("played", 0) + 1

    ranked = sorted(pts.keys(),
                    key=lambda t: (pts[t].get("pts",0), pts[t].get("nrr",0.0)),
                    reverse=True)
    return ranked, pts

def simulate_ipl_playoffs(model, le_t1, le_t2, le_venue, top4):
    """Simulate Q1 → Eliminator → Q2 → Final. Requires exactly 4 teams."""
    if len(top4) < 4:
        # Pad with random IPL teams if simulation produced fewer
        extras = [t for t in IPL_TEAMS if t not in top4]
        top4   = (top4 + extras)[:4]

    def win(a, b, stage="qualifier_1"):
        p = ipl_win_prob(model, le_t1, le_t2, le_venue, a, b, stage=stage)
        return a if random.random() < p else b

    q1w   = win(top4[0], top4[1], "qualifier_1")
    q1l   = top4[1] if q1w == top4[0] else top4[0]
    elim  = win(top4[2], top4[3], "eliminator")
    q2w   = win(q1l, elim, "qualifier_2")
    champ = win(q1w, q2w, "final")
    return champ

def run_ipl_simulation(n=N_SIMULATIONS, points_table=None, fixtures=None):
    print(f"\n🏏 IPL Simulator — {n:,} simulations")
    model, le_t1, le_t2, le_venue = load_ipl()

    # Use S3-loaded fixtures as defaults if none passed in request
    pts  = points_table if points_table else IPL_POINTS_TABLE
    fixs = fixtures     if fixtures     else IPL_REMAINING_FIXTURES

    if not pts:
        print("   ⚠ Empty points table — defaulting all teams to equal prior")
        pts = {t: {"played":7,"won":3,"lost":4,"nr":0,"pts":6,"nrr":0.0}
               for t in IPL_TEAMS}

    playoff_count  = defaultdict(int)
    champion_count = defaultdict(int)

    for _ in range(n):
        ranked, _ = simulate_ipl_season(model, le_t1, le_t2, le_venue, pts, fixs)
        top4 = ranked[:4]
        for t in top4:
            playoff_count[t] += 1
        champ = simulate_ipl_playoffs(model, le_t1, le_t2, le_venue, top4)
        champion_count[champ] += 1

    return {
        "playoff_probabilities":  {t: round(playoff_count[t]/n, 4)  for t in IPL_TEAMS},
        "champion_probabilities": {t: round(champion_count[t]/n, 4) for t in IPL_TEAMS},
        "simulations_run": n,
    }

# ═══════════════════════════════════════════════════════════════════════════════
#  FIFA SIMULATOR
# ═══════════════════════════════════════════════════════════════════════════════
def simulate_group_stage(model, le_home, le_away):
    standings     = {g: {t: {"pts":0,"gd":0,"gf":0} for t in ts}
                     for g, ts in FIFA_GROUPS.items()}
    team_to_group = {t: g for g, ts in FIFA_GROUPS.items() for t in ts}

    for fix in FIFA_GROUP_FIXTURES:
        # Handle (home, away, match_num, date) tuple format
        home, away = fix[0], fix[1]
        grp = team_to_group.get(home)
        if not grp: continue

        pw, pd, pl = fifa_wdl(model, le_home, le_away, home, away, "group")
        r = random.random()
        if r < pw:
            hg = random.randint(1,3); ag = random.randint(0, max(0,hg-1))
            standings[grp][home]["pts"] += 3
        elif r < pw+pd:
            hg = ag = random.randint(0,2)
            standings[grp][home]["pts"] += 1
            standings[grp][away]["pts"] += 1
        else:
            ag = random.randint(1,3); hg = random.randint(0, max(0,ag-1))
            standings[grp][away]["pts"] += 3

        standings[grp][home]["gd"] += hg-ag; standings[grp][home]["gf"] += hg
        standings[grp][away]["gd"] += ag-hg; standings[grp][away]["gf"] += ag

    ranked = {g: sorted(t.keys(),
                        key=lambda x: (t[x]["pts"],t[x]["gd"],t[x]["gf"]),
                        reverse=True)
              for g, t in standings.items()}
    return ranked, standings

def sim_ko(model, le_home, le_away, t1, t2, stage):
    pw, pd, pl = fifa_wdl(model, le_home, le_away, t1, t2, stage)
    r = random.random()
    if r < pw:    return t1
    if r < pw+pd: return t1 if random.random() < (0.5+(pw-pl)*0.1) else t2
    return t2

def run_fifa_simulation(n=N_SIMULATIONS):
    print(f"\n⚽ FIFA WC 2026 Simulator — {n:,} simulations")
    model, le_home, le_away = load_fifa()

    advance  = defaultdict(int)
    champion = defaultdict(int)
    all_teams = [t for ts in FIFA_GROUPS.values() for t in ts]

    for _ in range(n):
        ranked, standings = simulate_group_stage(model, le_home, le_away)

        thirds = sorted(
            [(teams[2], standings[g][teams[2]])
             for g, teams in ranked.items() if len(teams) >= 3],
            key=lambda x: (x[1]["pts"],x[1]["gd"],x[1]["gf"]), reverse=True
        )
        best3 = [t for t,_ in thirds[:8]]

        g1 = {g: ranked[g][0] for g in FIFA_GROUPS}
        g2 = {g: ranked[g][1] for g in FIFA_GROUPS}

        for g in FIFA_GROUPS:
            advance[g1[g]] += 1
            advance[g2[g]] += 1
        for t in best3:
            advance[t] += 1

        def b3(i): return best3[i] if i < len(best3) else g2[list(FIFA_GROUPS)[i % 12]]

        r32 = [
            (g2["A"],g2["B"]), (g1["F"],g2["C"]), (g1["C"],g2["F"]), (g2["E"],g2["I"]),
            (g1["J"],g2["H"]), (g2["K"],g2["L"]), (g1["A"],b3(0)),   (g1["I"],b3(1)),
            (g1["D"],b3(2)),   (g1["G"],b3(3)),   (g1["B"],b3(4)),   (g1["L"],b3(5)),
            (g1["E"],b3(6)),   (g1["H"],g2["J"]), (g2["D"],g2["G"]), (g1["K"],b3(7)),
        ]

        def play(pairs, stage):
            return [sim_ko(model, le_home, le_away, a, b, stage) for a,b in pairs]

        r32w = play(r32,                             "round_of_32")
        r16w = play(list(zip(r32w[::2],r32w[1::2])), "round_of_16")
        qfw  = play(list(zip(r16w[::2],r16w[1::2])), "quarterfinal")
        sfw  = play(list(zip(qfw[::2], qfw[1::2])),  "semifinal")
        champ = sim_ko(model, le_home, le_away, sfw[0], sfw[1], "final")
        champion[champ] += 1

    return {
        "group_qualification":  {t: round(advance[t]/n,  4) for t in all_teams},
        "champion_probability": {t: round(champion[t]/n, 4) for t in all_teams},
        "simulations_run": n,
    }

# ═══════════════════════════════════════════════════════════════════════════════
#  LAMBDA HANDLER
# ═══════════════════════════════════════════════════════════════════════════════
def clean(obj):
    if isinstance(obj, defaultdict):  return clean(dict(obj))
    if isinstance(obj, dict):         return {k: clean(v) for k,v in obj.items()}
    if isinstance(obj, (list,tuple)): return [clean(x) for x in obj]
    if isinstance(obj, np.integer):   return int(obj)
    if isinstance(obj, np.floating):  return float(obj)
    return obj

def _resp(status, body):
    return {"statusCode": status,
            "headers": {"Content-Type":"application/json","Access-Control-Allow-Origin":"*"},
            "body": json.dumps(body)}

def handler(event, context):
    try:
        body  = json.loads(event.get("body") or "{}")
        sport = body.get("sport", "ipl").lower()
        n     = min(int(body.get("simulations", 50)), 50)

        # Optional overrides from request body
        pts  = body.get("points_table")    # None → use S3-loaded IPL_POINTS_TABLE
        fixs = body.get("remaining_fixtures") # None → use S3-loaded IPL_REMAINING_FIXTURES

        if sport == "ipl":
            result = run_ipl_simulation(n, pts, fixs)
        elif sport == "fifa":
            result = run_fifa_simulation(n)
        elif sport == "both":
            result = {"ipl": run_ipl_simulation(n, pts, fixs),
                      "fifa": run_fifa_simulation(n)}
        else:
            return _resp(400, {"error": "sport must be ipl, fifa, or both"})

        return _resp(200, clean(result))

    except Exception as e:
        import traceback; traceback.print_exc()
        return _resp(500, {"error": str(e)})

# ═══════════════════════════════════════════════════════════════════════════════
#  LOCAL CLI
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sport", choices=["ipl","fifa","both"], default="both")
    parser.add_argument("--sims",  type=int, default=N_SIMULATIONS)
    args = parser.parse_args()

    results = {}
    if args.sport in ("ipl","both"):  results["ipl"]  = run_ipl_simulation(args.sims)
    if args.sport in ("fifa","both"): results["fifa"] = run_fifa_simulation(args.sims)

    with open("simulation_results.json","w") as f:
        json.dump(results, f, indent=2)
    print("\n✅ simulation_results.json saved")