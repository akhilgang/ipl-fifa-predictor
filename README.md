# Sports Predictor — IPL + FIFA World Cup 2026
AWS free-tier serverless stack. Single API, two sports, Monte Carlo simulation.

## API Endpoints
| Route           | Use                                          |
|-----------------|----------------------------------------------|
| POST /predict   | Single match prediction (IPL or FIFA)        |
| POST /simulate  | Monte Carlo qualification probabilities       |
| GET  /accuracy  | Live model accuracy tracker                  |

## Request Examples

### IPL single match
```json
POST /predict
{ "sport":"ipl", "team1":"Mumbai Indians", "team2":"Chennai Super Kings",
  "venue":"Wankhede Stadium", "stage":"league" }
```

### FIFA single match
```json
POST /predict
{ "sport":"fifa", "home_team":"Brazil", "away_team":"France", "stage":"semifinal" }
```

### IPL playoff qualification simulation
```json
POST /simulate
{ "sport":"ipl", "simulate":true,
  "points_table": {
    "Mumbai Indians":   {"pts":16,"nrr":0.45},
    "Chennai Super Kings": {"pts":14,"nrr":0.12},
    ...
  },
  "remaining_fixtures": [
    {"team1":"Mumbai Indians","team2":"CSK","venue":"Wankhede Stadium"},
    ...
  ]
}
```

### FIFA group qualification simulation
```json
POST /simulate
{ "sport":"fifa", "simulate":true }
```

## Deploy Steps
```bash
# 1. Train both models locally
python train_ipl.py
python train_fifa.py

# 2. Configure
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars

# 3. Deploy
terraform init && terraform apply

# 4. Upload models (command shown in terraform output)
aws s3 cp fifa_model.pkl   s3://BUCKET/fifa_model.pkl
aws s3 cp ipl_model.pkl    s3://BUCKET/ipl_model.pkl
# ... (all .pkl files)

# 5. Run full simulation locally (10k sims — faster than Lambda)
python simulators/simulator.py --sport both --sims 10000
```

## File Map
```
├── train_ipl.py              IPL training (Kaggle dataset)
├── train_fifa.py             FIFA training (Kaggle dataset)
├── fifa_fixtures.py          WC 2026 groups + fixtures from official PDF
├── ipl_fixtures.py           IPL 2026 teams + playoff schedule
├── simulators/
│   └── simulator.py          Monte Carlo — run locally for 10k sims
├── lambda_src/
│   └── predict_handler.py    Unified Lambda — routes by sport field
├── main.tf                   Root Terraform
├── variables.tf
├── outputs.tf
└── modules/
    ├── s3/                   Single bucket for all model artifacts
    ├── dynamodb/             4 tables: ipl/fifa × predictions/stats
    ├── lambda/               5 functions: predict, accuracy, simulate,
    │                         ipl_result_updater, fifa_result_updater
    ├── api_gateway/          3 routes: /predict, /accuracy, /simulate
    └── amplify/              UI hosting
```

## How Playoff Qualification Works
The simulator runs N independent season completions:
- Each remaining match: model.predict_proba() → random draw against probability
- IPL: accumulate points, rank top 4, simulate Q1→Eliminator→Q2→Final
- FIFA: accumulate pts/GD per group, advance top 2 + 8 best 3rd-place teams,
        simulate full bracket including penalties for drawn knockout matches
- Output: "MI qualifies in 73% of simulations" style probabilities
