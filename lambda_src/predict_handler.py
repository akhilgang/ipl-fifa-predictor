"""
predict_handler.py  —  unified, routes by sport field
POST /predict
Body examples:
  IPL:  {"sport":"ipl",  "team1":"Mumbai Indians", "team2":"CSK", "venue":"Wankhede Stadium"}
  FIFA: {"sport":"fifa", "home_team":"Brazil", "away_team":"France", "stage":"semifinal"}
  SIM:  {"sport":"ipl",  "simulate":true}   — runs Monte Carlo, returns qualification %
        {"sport":"fifa", "simulate":true}
"""

import boto3, joblib, io, json, os, random
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from copy import deepcopy

s3       = boto3.client("s3")
dynamo_r = boto3.resource("dynamodb")
BUCKET   = os.environ["MODEL_BUCKET"]

# ── Global artifact cache ─────────────────────────────────────────────────────
_cache = {}

def _load(key):
    if key not in _cache:
        _cache[key] = joblib.load(io.BytesIO(
            s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
        ))
    return _cache[key]

def get_ipl_artifacts():
    return (_load("ipl_model.pkl"), _load("ipl_le_t1.pkl"),
            _load("ipl_le_t2.pkl"), _load("ipl_le_venue.pkl"))

def get_fifa_artifacts():
    return (_load("fifa_model.pkl"), _load("fifa_le_home.pkl"),
            _load("fifa_le_away.pkl"))

# ── Feature builders ──────────────────────────────────────────────────────────
def _enc(le, val, fallback=0):
    try:    return int(le.transform([val])[0])
    except: return fallback

FIFA_STAGE_W = {"group":5,"round_of_32":6,"round_of_16":7,
                "quarterfinal":8,"semifinal":9,"final":10}
IPL_STAGE_W = {"league": 1, "playoff": 2, "eliminator": 2, "final": 3}

def ipl_features(t1, t2, venue, stage, t1_wr=0.5, t2_wr=0.5):
    model, le_t1, le_t2, le_venue = get_ipl_artifacts()
    stage_weight = IPL_STAGE_W.get(str(stage).lower(), 1)
    return [
        _enc(le_t1, t1),                          # 1  t1_enc
        _enc(le_t2, t2),                          # 2  t2_enc
        1,                                         # 3  toss_won_by_team1
        1,                                         # 4  toss_bat_first
        _enc(le_venue, venue) if venue else 0,    # 5  venue_enc
        stage_weight,                              # 6  stage_weight ← ADDED
        t1_wr,                                     # 7  t1_win_rate
        t2_wr,                                     # 8  t2_win_rate
        0,                                         # 9  t1_streak
        0,                                         # 10 t2_streak
        t1_wr - t2_wr,                            # 11 wr_diff
        0,                                         # 12 streak_diff
        0.5,                                       # 13 h2h_t1_win_rate
        2026,                                      # 14 season_num
    ], model

def fifa_features(home, away, stage, h_wr=0.45, a_wr=0.40):
    model, le_home, le_away = get_fifa_artifacts()
    tw = FIFA_STAGE_W.get(stage, 5)
    return [
        _enc(le_home, home), _enc(le_away, away), tw, 0,
        h_wr, a_wr, 0.1, -0.1,
        h_wr - a_wr, 0.2, 0.45,
    ], model

# ── Predict helpers ───────────────────────────────────────────────────────────
def predict_ipl(t1, t2, venue=None, stage="league"):
    feats, model = ipl_features(t1, t2, venue, stage)
    proba   = model.predict_proba([feats])[0]
    classes = list(model.classes_)
    p_t1    = float(proba[classes.index(1)])
    return {
        "winner":        t1 if p_t1 >= 0.5 else t2,
        "probabilities": {t1: round(p_t1, 4), t2: round(1-p_t1, 4)},
    }

def predict_fifa(home, away, stage="group"):
    feats, model = fifa_features(home, away, stage)
    proba   = model.predict_proba([feats])[0]
    classes = list(model.classes_)
    p = {c: round(float(v), 4) for c, v in zip(classes, proba)}
    return {
        "outcome":       max(p, key=p.get),
        "probabilities": p,
    }

# ── Simulate helpers (lightweight Monte Carlo, 1k runs in Lambda) ─────────────
N_SIM = 1000   # reduced for Lambda timeout — use simulator.py locally for 10k

def simulate_ipl(points_table, remaining_fixtures):
    model, le_t1, le_t2, le_venue = get_ipl_artifacts()
    playoff_count  = defaultdict(int)
    champion_count = defaultdict(int)

    for _ in range(N_SIM):
        pts = deepcopy(points_table)
        for fix in remaining_fixtures:
            t1, t2 = fix["team1"], fix["team2"]
            venue  = fix.get("venue")
            feats, m = ipl_features(t1, t2, venue, "league")
            proba    = m.predict_proba([feats])[0]
            p_t1     = float(proba[list(m.classes_).index(1)])
            winner   = t1 if random.random() < p_t1 else t2
            loser    = t2 if winner == t1 else t1
            pts[winner]["pts"] = pts.get(winner, {}).get("pts", 0) + 2

        ranked = sorted(pts.keys(),
                        key=lambda t: (pts[t].get("pts",0), pts[t].get("nrr",0)),
                        reverse=True)
        top4 = ranked[:4]
        for t in top4: playoff_count[t] += 1

        # Simulate playoffs
        def win(a, b):
            f, m = ipl_features(a, b, None, "playoff")
            p = float(m.predict_proba([f])[0][list(m.classes_).index(1)])
            return a if random.random() < p else b

        q1w = win(top4[0], top4[1]); q1l = top4[1] if q1w==top4[0] else top4[0]
        ew  = win(top4[2], top4[3])
        q2w = win(q1l, ew)
        champ = win(q1w, q2w)
        champion_count[champ] += 1

    teams = list(points_table.keys())
    return {
        "playoff_qualification": {t: round(playoff_count[t]/N_SIM*100, 1) for t in teams},
        "champion_probability":  {t: round(champion_count[t]/N_SIM*100, 1) for t in teams},
        "simulations_run": N_SIM,
    }

def simulate_fifa(current_results=None):
    model, le_home, le_away = get_fifa_artifacts()
    # Lightweight: just simulate group qualification
    from fifa_fixtures import FIFA_GROUPS, FIFA_GROUP_FIXTURES, resolve_team

    advance_count = defaultdict(int)
    champion_count = defaultdict(int)
    all_teams = [t for ts in FIFA_GROUPS.values() for t in ts]

    for _ in range(N_SIM):
        standings = {g: {t: {"pts":0,"gd":0} for t in ts}
                     for g, ts in FIFA_GROUPS.items()}
        team_to_group = {t: g for g, ts in FIFA_GROUPS.items() for t in ts}

        for (home, away, _, __) in FIFA_GROUP_FIXTURES:
            grp = team_to_group.get(home)
            if not grp: continue
            feats, m = fifa_features(home, away, "group")
            proba    = m.predict_proba([feats])[0]
            classes  = list(m.classes_)
            p = {c: float(v) for c, v in zip(classes, proba)}
            r = random.random()
            if r < p.get("win",0.33):
                standings[grp][home]["pts"] += 3
                standings[grp][home]["gd"]  += random.randint(1,3)
                standings[grp][away]["gd"]  -= random.randint(0,2)
            elif r < p.get("win",0.33) + p.get("draw",0.33):
                standings[grp][home]["pts"] += 1
                standings[grp][away]["pts"] += 1
            else:
                standings[grp][away]["pts"] += 3
                standings[grp][away]["gd"]  += random.randint(1,3)
                standings[grp][home]["gd"]  -= random.randint(0,2)

        for grp, table in standings.items():
            ranked = sorted(table.keys(),
                            key=lambda t: (table[t]["pts"], table[t]["gd"]),
                            reverse=True)
            advance_count[ranked[0]] += 1
            advance_count[ranked[1]] += 1
            # Simple champion: group winner of strongest group
            champion_count[ranked[0]] += 1

    return {
        "group_qualification": {t: round(advance_count[t]/N_SIM*100,1) for t in all_teams},
        "win_probability":     {t: round(champion_count[t]/N_SIM*100,1) for t in all_teams},
        "simulations_run": N_SIM,
    }

# ── DynamoDB logging ──────────────────────────────────────────────────────────
def log_prediction(sport, match_id, payload):
    table_name = os.environ.get(f"{sport.upper()}_PREDICTIONS_TABLE")
    if not table_name: return
    table = dynamo_r.Table(table_name)
    now = datetime.now(timezone.utc).isoformat()
    ttl = int((datetime.now(timezone.utc) + timedelta(days=90)).timestamp())
    table.put_item(Item={
        "match_id":  match_id, "timestamp": now,
        "sport":     sport,    "expires_at": ttl,
        "actual":    "PENDING","correct":   "PENDING",
        **{k: str(v) if isinstance(v, dict) else v for k, v in payload.items()}
    })

# ── Main handler ──────────────────────────────────────────────────────────────
def handler(event, context):
    try:
        body  = json.loads(event.get("body") or "{}")
        sport = body.get("sport", "").lower()

        if sport not in ("ipl", "fifa"):
            return _resp(400, {"error": "sport must be 'ipl' or 'fifa'"})

        # ── Simulation mode ───────────────────────────────────────────────────
        if body.get("simulate"):
            if sport == "ipl":
                pts  = body.get("points_table", {})
                fixes = body.get("remaining_fixtures", [])
                result = simulate_ipl(pts, fixes)
            else:
                result = simulate_fifa(body.get("current_results"))
            return _resp(200, {"sport": sport, "simulation": result})

        # ── Single match prediction ───────────────────────────────────────────
        if sport == "ipl":
            t1    = body.get("team1", "")
            t2    = body.get("team2", "")
            venue = body.get("venue")
            stage = body.get("stage", "league")
            if not t1 or not t2:
                return _resp(400, {"error": "team1 and team2 required for IPL"})
            result   = predict_ipl(t1, t2, venue, stage)
            match_id = f"IPL_{t1}_{t2}"
            log_prediction("ipl", match_id, {**result, "team1":t1,"team2":t2,"stage":stage})
            return _resp(200, {"sport":"ipl","team1":t1,"team2":t2,"stage":stage,**result})

        else:  # fifa
            home  = body.get("home_team","")
            away  = body.get("away_team","")
            stage = body.get("stage","group")
            if not home or not away:
                return _resp(400, {"error": "home_team and away_team required for FIFA"})
            result   = predict_fifa(home, away, stage)
            match_id = f"FIFA_{home}_{away}_{stage}"
            log_prediction("fifa", match_id, {**result,"home_team":home,"away_team":away,"stage":stage})
            return _resp(200, {"sport":"fifa","home_team":home,"away_team":away,"stage":stage,**result})

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback; traceback.print_exc()
        return _resp(500, {"error": str(e)})

def _resp(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type":"application/json","Access-Control-Allow-Origin":"*"},
        "body": json.dumps(body),
    }
