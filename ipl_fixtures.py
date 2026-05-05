"""
ipl_fixtures.py
IPL 2026 — teams, playoff schedule, and remaining fixtures template
Update REMAINING_FIXTURES and POINTS_TABLE with live data before simulation
"""

IPL_TEAMS = [
    "Mumbai Indians",
    "Chennai Super Kings",
    "Royal Challengers Bengaluru",
    "Kolkata Knight Riders",
    "Delhi Capitals",
    "Sunrisers Hyderabad",
    "Rajasthan Royals",
    "Punjab Kings",
    "Lucknow Super Giants",
    "Gujarat Titans",
]

# ── Playoff schedule (provided) ───────────────────────────────────────────────
IPL_PLAYOFF_SCHEDULE = {
    "qualifier_1": {
        "match":       "1st vs 2nd",
        "date":        "2026-05-26",
        "description": "Winner goes directly to Final"
    },
    "eliminator": {
        "match":       "3rd vs 4th",
        "date":        "2026-05-27",
        "description": "Loser is eliminated"
    },
    "qualifier_2": {
        "match":       "Loser Q1 vs Winner Eliminator",
        "date":        "2026-05-29",
        "description": "Winner goes to Final"
    },
    "final": {
        "match":       "Winner Q1 vs Winner Q2",
        "date":        "2026-05-31",
        "description": "IPL 2026 Champion"
    },
}

# ── Points table — UPDATE THIS with live standings before running simulator ───
# Format: {team: {played, won, lost, no_result, pts, nrr}}
# NRR = Net Run Rate (used as tiebreaker)
IPL_POINTS_TABLE = {
    "Mumbai Indians":               {"played": 0, "won": 0, "lost": 0, "nr": 0, "pts": 0, "nrr": 0.0},
    "Chennai Super Kings":          {"played": 0, "won": 0, "lost": 0, "nr": 0, "pts": 0, "nrr": 0.0},
    "Royal Challengers Bengaluru":  {"played": 0, "won": 0, "lost": 0, "nr": 0, "pts": 0, "nrr": 0.0},
    "Kolkata Knight Riders":        {"played": 0, "won": 0, "lost": 0, "nr": 0, "pts": 0, "nrr": 0.0},
    "Delhi Capitals":               {"played": 0, "won": 0, "lost": 0, "nr": 0, "pts": 0, "nrr": 0.0},
    "Sunrisers Hyderabad":          {"played": 0, "won": 0, "lost": 0, "nr": 0, "pts": 0, "nrr": 0.0},
    "Rajasthan Royals":             {"played": 0, "won": 0, "lost": 0, "nr": 0, "pts": 0, "nrr": 0.0},
    "Punjab Kings":                 {"played": 0, "won": 0, "lost": 0, "nr": 0, "pts": 0, "nrr": 0.0},
    "Lucknow Super Giants":         {"played": 0, "won": 0, "lost": 0, "nr": 0, "pts": 0, "nrr": 0.0},
    "Gujarat Titans":               {"played": 0, "won": 0, "lost": 0, "nr": 0, "pts": 0, "nrr": 0.0},
}

# ── Remaining fixtures — UPDATE with actual remaining schedule ────────────────
# Format: (team1, team2, venue)
# team1 = batting first / home side
IPL_REMAINING_FIXTURES = [
    # Example structure — replace with real remaining matches
    # ("Mumbai Indians", "Chennai Super Kings", "Wankhede Stadium"),
]
