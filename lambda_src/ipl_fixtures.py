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
    "Punjab Kings": {
        "played": 9,
        "won": 6,
        "lost": 2,
        "nr": 1,
        "pts": 13,
        "nrr": 0.855,
    },
    "Royal Challengers Bengaluru": {
        "played": 9,
        "won": 6,
        "lost": 3,
        "nr": 0,
        "pts": 12,
        "nrr": 1.420,
    },
    "Sunrisers Hyderabad": {
        "played": 10,
        "won": 6,
        "lost": 4,
        "nr": 0,
        "pts": 12,
        "nrr": 0.644,
    },
    "Rajasthan Royals": {
        "played": 10,
        "won": 6,
        "lost": 4,
        "nr": 0,
        "pts": 12,
        "nrr": 0.510,
    },
    "Gujarat Titans": {
        "played": 10,
        "won": 6,
        "lost": 4,
        "nr": 0,
        "pts": 12,
        "nrr": -0.147,
    },
    "Chennai Super Kings": {
        "played": 10,
        "won": 5,
        "lost": 5,
        "nr": 0,
        "pts": 10,
        "nrr": 0.151,
    },
    "Delhi Capitals": {
        "played": 10,
        "won": 4,
        "lost": 6,
        "nr": 0,
        "pts": 8,
        "nrr": -0.949,
    },
    "Kolkata Knight Riders": {
        "played": 9,
        "won": 3,
        "lost": 5,
        "nr": 1,
        "pts": 7,
        "nrr": -0.539,
    },
    "Mumbai Indians": {
        "played": 10,
        "won": 3,
        "lost": 7,
        "nr": 0,
        "pts": 6,
        "nrr": -0.649,
    },
    "Lucknow Super Giants": {
        "played": 9,
        "won": 2,
        "lost": 7,
        "nr": 0,
        "pts": 4,
        "nrr": -1.076,
    },
}

# ── Remaining fixtures — UPDATE with actual remaining schedule ────────────────
# Format: (team1, team2, venue)
# team1 = batting first / home side
# ── Remaining fixtures — extracted from image ────────────────────────────────
# Format: (team1, team2, venue)

IPL_REMAINING_FIXTURES = [

    ("Lucknow Super Giants", "Royal Challengers Bengaluru", "Lucknow"),
    ("Delhi Capitals", "Kolkata Knight Riders", "Delhi"),
    ("Rajasthan Royals", "Gujarat Titans", "Jaipur"),
    ("Chennai Super Kings", "Lucknow Super Giants", "Chennai"),
    ("Royal Challengers Bengaluru", "Mumbai Indians", "Raipur"),

    ("Punjab Kings", "Delhi Capitals", "Dharamshala"),
    ("Gujarat Titans", "Sunrisers Hyderabad", "Ahmedabad"),
    ("Royal Challengers Bengaluru", "Kolkata Knight Riders", "Raipur"),

    ("Punjab Kings", "Mumbai Indians", "Dharamshala"),
    ("Lucknow Super Giants", "Chennai Super Kings", "Lucknow"),

    ("Kolkata Knight Riders", "Gujarat Titans", "Kolkata"),
    ("Punjab Kings", "Royal Challengers Bengaluru", "Dharamshala"),

    ("Delhi Capitals", "Rajasthan Royals", "Delhi"),
    ("Chennai Super Kings", "Sunrisers Hyderabad", "Chennai"),

    ("Rajasthan Royals", "Lucknow Super Giants", "Jaipur"),
    ("Kolkata Knight Riders", "Mumbai Indians", "Kolkata"),

    ("Chennai Super Kings", "Gujarat Titans", "Chennai"),
    ("Sunrisers Hyderabad", "Royal Challengers Bengaluru", "Hyderabad"),

    ("Lucknow Super Giants", "Punjab Kings", "Lucknow"),
    ("Mumbai Indians", "Rajasthan Royals", "Mumbai"),

    ("Kolkata Knight Riders", "Delhi Capitals", "Kolkata"),
]
