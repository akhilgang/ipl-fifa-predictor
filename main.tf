terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws    = { source = "hashicorp/aws",  version = "~> 5.0" }
    archive = { source = "hashicorp/archive", version = "~> 2.0" }
    random = { source = "hashicorp/random",  version = "~> 3.0" }
  }
}

provider "aws" { region = var.aws_region }

# ── S3: single bucket, both models ───────────────────────────────────────────
module "s3" {
  source = "./modules/s3"
  project_name = var.project_name
  versioning   = true
}

# ── DynamoDB: 4 tables (predictions + stats per sport) ───────────────────────
module "dynamodb" {
  source       = "./modules/dynamodb"
  project_name = var.project_name
}

# ── Lambda: unified predict + accuracy + 2 result updaters ───────────────────
module "lambda" {
  source                   = "./modules/lambda"
  project_name             = var.project_name
  model_bucket             = module.s3.bucket_name
  ipl_predictions_table    = module.dynamodb.ipl_predictions_table_name
  ipl_stats_table          = module.dynamodb.ipl_stats_table_name
  fifa_predictions_table   = module.dynamodb.fifa_predictions_table_name
  fifa_stats_table         = module.dynamodb.fifa_stats_table_name
  log_retention_days       = var.log_retention_days
}

# ── API Gateway ───────────────────────────────────────────────────────────────
module "api_gateway" {
  source                     = "./modules/api_gateway"
  project_name               = var.project_name
  predict_lambda_invoke_arn  = module.lambda.predict_invoke_arn
  predict_lambda_name        = module.lambda.predict_function_name
  accuracy_lambda_invoke_arn = module.lambda.accuracy_invoke_arn
  accuracy_lambda_name       = module.lambda.accuracy_function_name
  simulate_lambda_invoke_arn = module.lambda.simulate_invoke_arn
  simulate_lambda_name       = module.lambda.simulate_function_name
}

# # ── Amplify UI ────────────────────────────────────────────────────────────────
module "amplify" {
  source          = "./modules/amplify"
  project_name    = var.project_name
  # app_name = "${var.project_name}-ui"
  api_gateway_url = module.api_gateway.api_url
  github_repo     = var.github_repo
  github_token    = var.github_token
  branch          = var.github_branch
}

# ── EventBridge: IPL result poller (every 2h during May) ─────────────────────
resource "aws_cloudwatch_event_rule" "ipl_poller" {
  name                = "${var.project_name}-ipl-result-poller"
  description         = "Poll IPL results every 2 hours"
  schedule_expression = "rate(2 hours)"
}
resource "aws_cloudwatch_event_target" "ipl_poller" {
  rule = aws_cloudwatch_event_rule.ipl_poller.name
  arn  = module.lambda.ipl_result_updater_arn
}
resource "aws_lambda_permission" "ipl_eventbridge" {
  statement_id  = "AllowEventBridgeIPL"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda.ipl_result_updater_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ipl_poller.arn
}

# ── EventBridge: FIFA result poller (every 2h during June-July) ───────────────
resource "aws_cloudwatch_event_rule" "fifa_poller" {
  name                = "${var.project_name}-fifa-result-poller"
  description         = "Poll FIFA World Cup results every 2 hours"
  schedule_expression = "rate(2 hours)"
}
resource "aws_cloudwatch_event_target" "fifa_poller" {
  rule = aws_cloudwatch_event_rule.fifa_poller.name
  arn  = module.lambda.fifa_result_updater_arn
}
resource "aws_lambda_permission" "fifa_eventbridge" {
  statement_id  = "AllowEventBridgeFIFA"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda.fifa_result_updater_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.fifa_poller.arn
}

# ── Budget alert: $1 threshold — catches any surprise spend early ─────────────
resource "aws_budgets_budget" "zero_spend_alert" {
  name         = "${var.project_name}-budget-alert"
  budget_type  = "COST"
  limit_amount = "1"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }
}
