"""
predict_handler.py
POST /predict  — single match prediction (IPL or FIFA)
POST /simulate — routes to simulator.py handler
"""

import boto3, joblib, io, json, os
from datetime import datetime, timezone, timedelta

s3     = boto3.client("s3")
dynamo = boto3.resource("dynamodb")
BUCKET = os.environ["MODEL_BUCKET"]

_cache = {}

def _load(key):
    if key not in _cache:
        obj = s3.get_object(Bucket=BUCKET, Key=key)
        _cache[key] = joblib.load(io.BytesIO(obj["Body"].read()))
    return _cache[key]

def _enc(le, val, fallback=0):
    try:    return int(le.transform([val])[0])
    except: return fallback

# ── IPL: 14 features — must match train_ipl.py EXACTLY ───────────────────────
# t1_enc, t2_enc, toss_won_by_team1, toss_bat_first, venue_enc, stage_weight,
# t1_win_rate, t2_win_rate, t1_streak, t2_streak, wr_diff, streak_diff,
# h2h_t1_win_rate, season_num

IPL_STAGE_WEIGHT = {"league":1,"qualifier_1":2,"eliminator":2,"qualifier_2":2,"final":3}

def predict_ipl(body):
    t1    = body.get("team1", "")
    t2    = body.get("team2", "")
    venue = body.get("venue", "")
    stage = body.get("stage", "league")

    if not t1 or not t2:
        return None, "team1 and team2 are required"

    model    = _load("ipl_model.pkl")
    le_t1    = _load("ipl_le_t1.pkl")
    le_t2    = _load("ipl_le_t2.pkl")
    le_venue = _load("ipl_le_venue.pkl")

    t1_enc = _enc(le_t1,    t1)
    t2_enc = _enc(le_t2,    t2)
    v_enc  = _enc(le_venue, venue)
    sw     = IPL_STAGE_WEIGHT.get(stage, 1)

    # Default form values — no live rolling data at prediction time
    t1_wr, t2_wr     = 0.5, 0.5
    t1_st, t2_st     = 0, 0
    wr_diff, st_diff = 0.0, 0
    h2h              = 0.5

    features = [
        t1_enc, t2_enc,          # 1-2
        1, 1,                    # 3-4  toss (defaults)
        v_enc, sw,               # 5-6
        t1_wr, t2_wr,            # 7-8
        t1_st, t2_st,            # 9-10
        wr_diff, st_diff,        # 11-12
        h2h,                     # 13
        2026,                    # 14
    ]

    proba   = model.predict_proba([features])[0]
    classes = list(model.classes_)
    p_t1    = float(proba[classes.index(1)])

    winner = t1 if p_t1 >= 0.5 else t2
    probs  = {t1: round(p_t1, 4), t2: round(1 - p_t1, 4)}

    match_id = f"IPL_{t1}_{t2}_{stage}"
    _log("ipl", match_id, {"team1":t1,"team2":t2,"stage":stage,
                            "predicted":winner,"probabilities":str(probs)})

    return {"sport":"ipl","match_id":match_id,"team1":t1,"team2":t2,
            "stage":stage,"winner":winner,"probabilities":probs}, None


# ── FIFA: 11 features — must match train_fifa.py EXACTLY ─────────────────────
# home_enc, away_enc, tournament_weight, is_neutral,
# home_win_rate, away_win_rate, home_avg_gd, away_avg_gd,
# wr_diff, gd_diff, h2h_home_win_rate

FIFA_STAGE_WEIGHT = {
    "group":5,"round_of_32":6,"round_of_16":7,
    "quarterfinal":8,"semifinal":9,"final":10
}

TEAM_ALIASES = {
    "Korea Republic":"South Korea","Czechia":"Czech Republic",
    "Bosnia Herzegovina":"Bosnia-Herzegovina","Cote dIvoire":"Ivory Coast",
    "Congo DR":"DR Congo","IR Iran":"Iran","Cabo Verde":"Cape Verde",
}

def predict_fifa(body):
    home  = body.get("home_team", "")
    away  = body.get("away_team", "")
    stage = body.get("stage", "group")

    if not home or not away:
        return None, "home_team and away_team are required"

    model   = _load("fifa_model.pkl")
    le_home = _load("fifa_le_home.pkl")
    le_away = _load("fifa_le_away.pkl")

    h_enc = _enc(le_home, TEAM_ALIASES.get(home, home))
    a_enc = _enc(le_away, TEAM_ALIASES.get(away, away))
    tw    = FIFA_STAGE_WEIGHT.get(stage, 5)

    features = [
        h_enc, a_enc,       # 1-2
        tw, 0,              # 3-4  tournament_weight, is_neutral
        0.45, 0.40,         # 5-6  home_win_rate, away_win_rate
        0.1, -0.1,          # 7-8  home_avg_gd, away_avg_gd
        0.05,               # 9   wr_diff
        0.2,                # 10  gd_diff
        0.45,               # 11  h2h_home_win_rate
    ]

    proba   = model.predict_proba([features])[0]
    classes = list(model.classes_)
    probs   = {c: round(float(v), 4) for c, v in zip(classes, proba)}
    outcome = max(probs, key=probs.get)

    match_id = f"FIFA_{home}_{away}_{stage}"
    _log("fifa", match_id, {"home_team":home,"away_team":away,"stage":stage,
                             "predicted":outcome,"probabilities":str(probs)})

    return {"sport":"fifa","match_id":match_id,"home_team":home,"away_team":away,
            "stage":stage,"outcome":outcome,"probabilities":probs}, None


# ── DynamoDB logging ──────────────────────────────────────────────────────────
def _log(sport, match_id, payload):
    try:
        tbl_key = f"{sport.upper()}_PREDICTIONS_TABLE"
        tbl     = dynamo.Table(os.environ[tbl_key])
        now     = datetime.now(timezone.utc).isoformat()
        ttl     = int((datetime.now(timezone.utc) + timedelta(days=90)).timestamp())
        tbl.put_item(Item={
            "match_id": match_id, "timestamp": now,
            "sport": sport, "actual": "PENDING",
            "correct": "PENDING", "expires_at": ttl,
            **payload
        })
    except Exception as e:
        print(f"DynamoDB log failed: {e}")


# ── Main handler ──────────────────────────────────────────────────────────────
def handler(event, context):
    try:
        body  = json.loads(event.get("body") or "{}")
        sport = body.get("sport", "").lower()

        # Simulate route
        if body.get("simulate"):
            from simulator import handler as sim_handler
            return sim_handler(event, context)

        if sport == "ipl":
            result, err = predict_ipl(body)
        elif sport == "fifa":
            result, err = predict_fifa(body)
        else:
            return _resp(400, {"error": "sport must be 'ipl' or 'fifa'"})

        if err:
            return _resp(400, {"error": err})
        return _resp(200, result)

    except Exception as e:
        import traceback; traceback.print_exc()
        return _resp(500, {"error": str(e)})

def _resp(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type":"application/json","Access-Control-Allow-Origin":"*"},
        "body": json.dumps(body),
    }