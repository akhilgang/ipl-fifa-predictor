"""
simulator.py
Monte Carlo Tournament Simulator
- IPL: top-4 playoff qualification probabilities
- FIFA: group qualification + full knockout bracket win probabilities
Run: python simulator.py --sport ipl
     python simulator.py --sport fifa
     python simulator.py --sport both
"""

import argparse
import random
import json
import joblib
import numpy as np
from collections import defaultdict
from copy import deepcopy

from fifa_fixtures import (FIFA_GROUPS, FIFA_GROUP_FIXTURES,
                            KNOCKOUT_SCHEDULE, resolve_team)
from ipl_fixtures  import (IPL_TEAMS, IPL_POINTS_TABLE,
                            IPL_REMAINING_FIXTURES, IPL_PLAYOFF_SCHEDULE)

N_SIMULATIONS = 10_000   # increase to 50k for tighter confidence intervals

# ═══════════════════════════════════════════════════════════════════════════════
#  SHARED: load models
# ═══════════════════════════════════════════════════════════════════════════════

def load_ipl_model():
    model    = joblib.load("ipl_model.pkl")
    le_t1    = joblib.load("ipl_le_t1.pkl")
    le_t2    = joblib.load("ipl_le_t2.pkl")
    try:
        le_venue = joblib.load("ipl_le_venue.pkl")
    except FileNotFoundError:
        le_venue = None
    return model, le_t1, le_t2, le_venue

def load_fifa_model():
    model    = joblib.load("fifa_model.pkl")
    le_home  = joblib.load("fifa_le_home.pkl")
    le_away  = joblib.load("fifa_le_away.pkl")
    return model, le_home, le_away


# ═══════════════════════════════════════════════════════════════════════════════
#  IPL SIMULATOR
# ═══════════════════════════════════════════════════════════════════════════════

def ipl_predict_win_prob(model, le_t1, le_t2, le_venue, team1, team2, venue=None):
    """Return probability that team1 wins."""
    def enc(le, val, fallback=0):
        try: return le.transform([val])[0]
        except: return fallback

    t1_enc  = enc(le_t1, team1)
    t2_enc  = enc(le_t2, team2)
    v_enc   = enc(le_venue, venue) if le_venue and venue else 0

    # Default form features — in production, pull from live points table
    features = [t1_enc, t2_enc, 1, 1, v_enc,
                0.5, 0.5, 0, 0, 0.0, 0.0, 0.5, 2026]

    proba = model.predict_proba([features])[0]
    classes = list(model.classes_)
    return float(proba[classes.index(1)])  # prob team1 wins


def simulate_ipl_season(model, le_t1, le_t2, le_venue,
                         current_points, remaining_fixtures):
    """
    Simulate remaining IPL league stage.
    Returns final points table dict sorted by pts desc, nrr desc.
    """
    pts = deepcopy(current_points)

    for (t1, t2, *venue_args) in remaining_fixtures:
        venue = venue_args[0] if venue_args else None
        p_win = ipl_predict_win_prob(model, le_t1, le_t2, le_venue, t1, t2, venue)
        if random.random() < p_win:
            pts[t1]["pts"] += 2; pts[t1]["won"] += 1
            pts[t2]["lost"] += 1
        else:
            pts[t2]["pts"] += 2; pts[t2]["won"] += 1
            pts[t1]["lost"] += 1

    # Sort: pts desc, then nrr desc (tiebreaker)
    ranked = sorted(pts.keys(),
                    key=lambda t: (pts[t]["pts"], pts[t]["nrr"]),
                    reverse=True)
    return ranked, pts


def simulate_ipl_playoffs(model, le_t1, le_t2, le_venue, top4):
    """
    Simulate Q1 → Eliminator → Q2 → Final.
    Returns predicted champion.
    """
    def win(t1, t2):
        p = ipl_predict_win_prob(model, le_t1, le_t2, le_venue, t1, t2)
        return t1 if random.random() < p else t2

    # Qualifier 1: 1st vs 2nd — winner goes to final
    q1_winner = win(top4[0], top4[1])
    q1_loser  = top4[1] if q1_winner == top4[0] else top4[0]

    # Eliminator: 3rd vs 4th — loser eliminated
    elim_winner = win(top4[2], top4[3])

    # Qualifier 2: Q1 loser vs Eliminator winner
    q2_winner = win(q1_loser, elim_winner)

    # Final
    champion = win(q1_winner, q2_winner)
    return champion, q1_winner, q2_winner


def run_ipl_simulation(n=N_SIMULATIONS):
    print(f"\n🏏 IPL Simulator — {n:,} simulations")
    model, le_t1, le_t2, le_venue = load_ipl_model()

    playoff_count  = defaultdict(int)   # times team finished top 4
    champion_count = defaultdict(int)   # times team won IPL
    finish_pos     = defaultdict(lambda: defaultdict(int))

    for i in range(n):
        ranked, pts = simulate_ipl_season(
            model, le_t1, le_t2, le_venue,
            IPL_POINTS_TABLE, IPL_REMAINING_FIXTURES
        )
        top4 = ranked[:4]
        for t in top4:
            playoff_count[t] += 1
        for pos, team in enumerate(ranked):
            finish_pos[team][pos+1] += 1

        champion, _, _ = simulate_ipl_playoffs(model, le_t1, le_t2, le_venue, top4)
        champion_count[champion] += 1

    print(f"\n{'Team':<35} {'Playoff%':>9} {'Champion%':>10} {'Avg Finish':>11}")
    print("─" * 70)
    for team in sorted(IPL_TEAMS, key=lambda t: -playoff_count[t]):
        playoff_pct  = playoff_count[team]  / n * 100
        champ_pct    = champion_count[team] / n * 100
        avg_finish   = sum(pos * cnt for pos, cnt in finish_pos[team].items()) / n
        print(f"  {team:<33} {playoff_pct:>8.1f}%  {champ_pct:>9.1f}%  {avg_finish:>10.2f}")

    print(f"\n🏆 Most likely champion: {max(champion_count, key=champion_count.get)}")
    print(f"   ({champion_count[max(champion_count, key=champion_count.get)]/n*100:.1f}% of simulations)")

    return {
        "playoff_probabilities":  {t: round(playoff_count[t]/n, 4)  for t in IPL_TEAMS},
        "champion_probabilities": {t: round(champion_count[t]/n, 4) for t in IPL_TEAMS},
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  FIFA SIMULATOR
# ═══════════════════════════════════════════════════════════════════════════════

def fifa_predict_proba(model, le_home, le_away, home, away, stage="group"):
    """Return (p_win, p_draw, p_loss) for home team."""
    STAGE_W = {"group":5,"round_of_32":6,"round_of_16":7,
               "quarterfinal":8,"semifinal":9,"final":10}

    def enc(le, val):
        resolved = resolve_team(val)
        try:    return le.transform([resolved])[0]
        except: return 0

    h_enc = enc(le_home, home)
    a_enc = enc(le_away, away)
    tw    = STAGE_W.get(stage, 5)

    features = [h_enc, a_enc, tw, 0, 0.45, 0.40, 0.1, -0.1, 0.05, 0.2, 0.45]
    proba   = model.predict_proba([features])[0]
    classes = list(model.classes_)
    p = {c: float(p) for c, p in zip(classes, proba)}
    return p.get("win",0.33), p.get("draw",0.34), p.get("loss",0.33)


def simulate_group_stage(model, le_home, le_away):
    """
    Simulate all 72 group stage matches.
    Returns dict: group -> ranked list of teams with pts/gd.
    """
    # Initialize standings per group
    standings = {}
    for grp, teams in FIFA_GROUPS.items():
        standings[grp] = {t: {"pts":0,"gd":0,"gf":0} for t in teams}

    # Find which group a team belongs to
    team_to_group = {t: g for g, ts in FIFA_GROUPS.items() for t in ts}

    for (home, away, match_num, date) in FIFA_GROUP_FIXTURES:
        grp = team_to_group.get(home)
        if not grp:
            continue

        pw, pd, pl = fifa_predict_proba(model, le_home, le_away, home, away, "group")

        # Simulate goals (Poisson-like from win prob)
        r = random.random()
        if r < pw:       # home wins
            hg = random.randint(1, 3); ag = random.randint(0, hg-1)
            standings[grp][home]["pts"] += 3
        elif r < pw+pd:  # draw
            hg = ag = random.randint(0, 2)
            standings[grp][home]["pts"] += 1
            standings[grp][away]["pts"] += 1
        else:            # away wins
            ag = random.randint(1, 3); hg = random.randint(0, ag-1)
            standings[grp][away]["pts"] += 3

        for t, g, c in [(home, hg, ag), (away, ag, hg)]:
            if t in standings[grp]:
                standings[grp][t]["gd"] += (g - c)
                standings[grp][t]["gf"] += g

    # Rank each group: pts desc, gd desc, gf desc
    ranked = {}
    for grp, table in standings.items():
        ranked[grp] = sorted(table.keys(),
                             key=lambda t: (table[t]["pts"],
                                            table[t]["gd"],
                                            table[t]["gf"]),
                             reverse=True)
    return ranked, standings


def best_third_place_teams(standings, ranked):
    """
    FIFA 2026 has 12 groups — top 2 from each advance (24 teams).
    8 more spots filled by best 3rd-place teams across all groups.
    Returns list of 8 best 3rd-place teams.
    """
    third_place = []
    for grp, teams in ranked.items():
        if len(teams) >= 3:
            t = teams[2]
            third_place.append((t, standings[grp][t]))

    # Sort 3rd-place teams by pts, gd, gf
    third_place.sort(key=lambda x: (x[1]["pts"], x[1]["gd"], x[1]["gf"]), reverse=True)
    return [t for t, _ in third_place[:8]]


def simulate_knockout_match(model, le_home, le_away, team1, team2, stage):
    """No draws in knockout — use penalty shootout tiebreak."""
    pw, pd, pl = fifa_predict_proba(model, le_home, le_away, team1, team2, stage)
    r = random.random()
    if r < pw:
        return team1
    elif r < pw + pd:
        # Penalties — treat as 50/50 adjusted by slight win-prob lean
        return team1 if random.random() < (0.5 + (pw-pl)*0.1) else team2
    else:
        return team2


def simulate_full_tournament(model, le_home, le_away):
    """Simulate group stage + full knockout bracket. Returns champion."""
    ranked, standings = simulate_group_stage(model, le_home, le_away)
    best_thirds       = best_third_place_teams(standings, ranked)

    # Build round of 32 bracket
    # Group winners (1A–1L), runners-up (2A–2L), best 3rd-place
    group_1st = {g: ranked[g][0] for g in FIFA_GROUPS}
    group_2nd = {g: ranked[g][1] for g in FIFA_GROUPS}

    # Simplified bracket seeding (mirrors PDF structure)
    # Round of 32 matchups from PDF
    r32_pairs = [
        (group_2nd["A"], group_2nd["B"]),
        (group_1st["F"], group_2nd["C"]),
        (group_1st["C"], group_2nd["F"]),
        (group_2nd["E"], group_2nd["I"]),
        (group_1st["J"], group_2nd["H"]),
        (group_2nd["K"], group_2nd["L"]),
        (group_1st["A"], best_thirds[0] if best_thirds else group_2nd["A"]),
        (group_1st["I"], best_thirds[1] if len(best_thirds)>1 else group_2nd["I"]),
        (group_1st["D"], best_thirds[2] if len(best_thirds)>2 else group_2nd["D"]),
        (group_1st["G"], best_thirds[3] if len(best_thirds)>3 else group_2nd["G"]),
        (group_1st["B"], best_thirds[4] if len(best_thirds)>4 else group_2nd["B"]),
        (group_1st["L"], best_thirds[5] if len(best_thirds)>5 else group_2nd["L"]),
        (group_1st["E"], best_thirds[6] if len(best_thirds)>6 else group_2nd["E"]),
        (group_1st["H"], group_2nd["J"]),
        (group_2nd["D"], group_2nd["G"]),
        (group_1st["K"], best_thirds[7] if len(best_thirds)>7 else group_2nd["K"]),
    ]

    def play_round(pairs, stage):
        winners = []
        for t1, t2 in pairs:
            winners.append(simulate_knockout_match(model, le_home, le_away, t1, t2, stage))
        return winners

    r32_winners  = play_round(r32_pairs,          "round_of_32")
    r16_pairs    = list(zip(r32_winners[::2], r32_winners[1::2]))
    r16_winners  = play_round(r16_pairs,           "round_of_16")
    qf_pairs     = list(zip(r16_winners[::2], r16_winners[1::2]))
    qf_winners   = play_round(qf_pairs,            "quarterfinal")
    sf_pairs     = list(zip(qf_winners[::2], qf_winners[1::2]))
    sf_winners   = play_round(sf_pairs,            "semifinal")
    champion     = simulate_knockout_match(
        model, le_home, le_away, sf_winners[0], sf_winners[1], "final"
    )
    return champion, group_1st, group_2nd


def run_fifa_simulation(n=N_SIMULATIONS):
    print(f"\n⚽ FIFA World Cup 2026 Simulator — {n:,} simulations")
    model, le_home, le_away = load_fifa_model()

    champion_count  = defaultdict(int)
    group_advance   = defaultdict(int)   # times team finished top 2 in group
    all_teams_flat  = [t for ts in FIFA_GROUPS.values() for t in ts]

    for i in range(n):
        champion, g1st, g2nd = simulate_full_tournament(model, le_home, le_away)
        champion_count[champion] += 1
        for grp in FIFA_GROUPS:
            group_advance[g1st[grp]] += 1
            group_advance[g2nd[grp]] += 1

    # Print group qualification table
    print(f"\n{'Team':<30} {'Group Advance%':>15} {'Win Tournament%':>16}")
    print("─" * 65)
    for grp, teams in FIFA_GROUPS.items():
        print(f"\n  ── Group {grp} ──")
        for team in teams:
            adv_pct  = group_advance[team]  / n * 100
            champ_pct = champion_count[team] / n * 100
            bar = "█" * int(champ_pct / 2)
            print(f"  {team:<28} {adv_pct:>13.1f}%  {champ_pct:>14.1f}%  {bar}")

    top_5 = sorted(champion_count.items(), key=lambda x: -x[1])[:5]
    print(f"\n🏆 Top 5 predicted champions:")
    for i, (team, cnt) in enumerate(top_5, 1):
        print(f"   {i}. {team:<28} {cnt/n*100:.1f}%")

    return {
        "group_qualification": {t: round(group_advance[t]/n, 4)  for t in all_teams_flat},
        "champion_probability":{t: round(champion_count[t]/n, 4) for t in all_teams_flat},
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sport", choices=["ipl","fifa","both"], default="both")
    parser.add_argument("--sims",  type=int, default=N_SIMULATIONS)
    args = parser.parse_args()

    results = {}
    if args.sport in ("ipl", "both"):
        results["ipl"]  = run_ipl_simulation(args.sims)
    if args.sport in ("fifa", "both"):
        results["fifa"] = run_fifa_simulation(args.sims)

    with open("simulation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n✅ Results saved to simulation_results.json")
