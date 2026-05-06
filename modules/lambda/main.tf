variable "project_name"             { type=string }
variable "model_bucket"              { type=string }
variable "ipl_predictions_table"    { type=string }
variable "ipl_stats_table"          { type=string }
variable "fifa_predictions_table"   { type=string }
variable "fifa_stats_table"         { type=string }
variable "log_retention_days"       { type=number }
# variable "football_data_api_key"    { type=string; sensitive=true; default="" }
# variable "cricbuzz_api_key"         { type=string; sensitive=true; default="" }
variable "layer_zip_path" {
  type    = string
  default = "sklearn-layer/ml-deps/sklearn-layer.zip"
}
# ── Lambda Layer: scikit-learn + joblib + numpy ───────────────────────────────
resource "aws_lambda_layer_version" "sklearn" {
  # filename            = var.layer_zip_path
  s3_bucket           = var.model_bucket
  s3_key              = "sklearn-layer/ml-deps/sklearn-layer.zip"
  source_code_hash    = filebase64sha256(var.layer_zip_path)
  layer_name          = "${var.project_name}-sklearn"
  compatible_runtimes = ["python3.12"]
  description         = "scikit-learn, joblib, numpy for Lambda"
}
# ── Shared IAM role ───────────────────────────────────────────────────────────
resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_exec.id
  policy = jsonencode({
    Version="2012-10-17"
    Statement=[
      { Effect="Allow"
        Action=["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"]
        Resource="arn:aws:logs:*:*:log-group:/aws/lambda/${var.project_name}*" },
      { Effect="Allow"
        Action=["s3:GetObject"]
        Resource="arn:aws:s3:::${var.model_bucket}/*" },
      { Effect="Allow"
        Action=["dynamodb:PutItem","dynamodb:GetItem","dynamodb:UpdateItem",
                "dynamodb:Scan","dynamodb:Query"]
        Resource=[
          "arn:aws:dynamodb:*:*:table/${var.ipl_predictions_table}",
          "arn:aws:dynamodb:*:*:table/${var.ipl_stats_table}",
          "arn:aws:dynamodb:*:*:table/${var.fifa_predictions_table}",
          "arn:aws:dynamodb:*:*:table/${var.fifa_stats_table}",
        ]},
    ]
  })
}

# ── Shared env vars ───────────────────────────────────────────────────────────
locals {
  common_env = {
    MODEL_BUCKET             = var.model_bucket
    IPL_PREDICTIONS_TABLE    = var.ipl_predictions_table
    IPL_STATS_TABLE          = var.ipl_stats_table
    FIFA_PREDICTIONS_TABLE   = var.fifa_predictions_table
    FIFA_STATS_TABLE         = var.fifa_stats_table
  }
  layers = [aws_lambda_layer_version.sklearn.arn]
}

# ── Zip source files ──────────────────────────────────────────────────────────
data "archive_file" "predict" {
  type        = "zip"
  output_path = "${path.module}/../../lambda_src/predict.zip"
  source_dir  = "${path.module}/../../lambda_src"
}

# ── 1. Predict (unified IPL + FIFA) ──────────────────────────────────────────
resource "aws_lambda_function" "predict" {
  function_name    = "${var.project_name}-predict"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "predict_handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.predict.output_path
  source_code_hash = data.archive_file.predict.output_base64sha256
  memory_size      = 512
  layers = local.layers
  timeout          = 30
  environment { variables = local.common_env }
}
resource "aws_cloudwatch_log_group" "predict" {
  name              = "/aws/lambda/${aws_lambda_function.predict.function_name}"
  retention_in_days = var.log_retention_days
}

# ── 2. Accuracy ───────────────────────────────────────────────────────────────
resource "aws_lambda_function" "accuracy" {
  function_name    = "${var.project_name}-accuracy"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "accuracy_handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.predict.output_path
  source_code_hash = data.archive_file.predict.output_base64sha256
  memory_size      = 128
  timeout          = 10
  layers = local.layers
  environment { variables = local.common_env }
}
resource "aws_cloudwatch_log_group" "accuracy" {
  name              = "/aws/lambda/${aws_lambda_function.accuracy.function_name}"
  retention_in_days = var.log_retention_days
}

# ── 3. Simulate (Monte Carlo via API) ─────────────────────────────────────────
resource "aws_lambda_function" "simulate" {
  function_name    = "${var.project_name}-simulate"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "simulator_handler.handler"   # same handler, simulate=true in body
  runtime          = "python3.12"
  filename         = data.archive_file.predict.output_path
  source_code_hash = data.archive_file.predict.output_base64sha256
  memory_size      = 512
  timeout          = 60   # Monte Carlo needs more time
  layers = local.layers
  environment { variables = local.common_env }
}
resource "aws_cloudwatch_log_group" "simulate" {
  name              = "/aws/lambda/${aws_lambda_function.simulate.function_name}"
  retention_in_days = var.log_retention_days
}

# ── 4. IPL result updater ─────────────────────────────────────────────────────
resource "aws_lambda_function" "ipl_result_updater" {
  function_name    = "${var.project_name}-ipl-result-updater"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "ipl_result_updater.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.predict.output_path
  source_code_hash = data.archive_file.predict.output_base64sha256
  memory_size      = 128
  timeout          = 60
  layers = local.layers
  environment { variables = local.common_env }
}
resource "aws_cloudwatch_log_group" "ipl_result_updater" {
  name              = "/aws/lambda/${aws_lambda_function.ipl_result_updater.function_name}"
  retention_in_days = var.log_retention_days
}

# ── 5. FIFA result updater ────────────────────────────────────────────────────
resource "aws_lambda_function" "fifa_result_updater" {
  function_name    = "${var.project_name}-fifa-result-updater"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "fifa_result_updater.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.predict.output_path
  source_code_hash = data.archive_file.predict.output_base64sha256
  memory_size      = 128
  timeout          = 60
  layers = local.layers
  environment { variables = local.common_env }
}
resource "aws_cloudwatch_log_group" "fifa_result_updater" {
  name              = "/aws/lambda/${aws_lambda_function.fifa_result_updater.function_name}"
  retention_in_days = var.log_retention_days
}

# ── Outputs ───────────────────────────────────────────────────────────────────
output "predict_invoke_arn"        { value = aws_lambda_function.predict.invoke_arn }
output "predict_function_name"     { value = aws_lambda_function.predict.function_name }
output "accuracy_invoke_arn"       { value = aws_lambda_function.accuracy.invoke_arn }
output "accuracy_function_name"    { value = aws_lambda_function.accuracy.function_name }
output "simulate_invoke_arn"       { value = aws_lambda_function.simulate.invoke_arn }
output "simulate_function_name"    { value = aws_lambda_function.simulate.function_name }
output "ipl_result_updater_arn"   { value = aws_lambda_function.ipl_result_updater.arn }
output "ipl_result_updater_name"  { value = aws_lambda_function.ipl_result_updater.function_name }
output "fifa_result_updater_arn"  { value = aws_lambda_function.fifa_result_updater.arn }
output "fifa_result_updater_name" { value = aws_lambda_function.fifa_result_updater.function_name }
