variable "project_name"                 { type=string }
variable "predict_lambda_invoke_arn"     { type=string }
variable "predict_lambda_name"           { type=string }
variable "accuracy_lambda_invoke_arn"    { type=string }
variable "accuracy_lambda_name"          { type=string }
variable "simulate_lambda_invoke_arn"    { type=string }
variable "simulate_lambda_name"          { type=string }

resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_headers = ["Content-Type","Authorization"]
    allow_methods = ["GET","POST","OPTIONS"]
    allow_origins = ["*"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId = "$context.requestId"
      ip = "$context.identity.sourceIp"
      requestTime = "$context.requestTime"
      httpMethod = "$context.httpMethod"
      routeKey = "$context.routeKey"
      status = "$context.status"
      protocol = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${var.project_name}"
  retention_in_days = 7
}

# ── Helper to create route + integration + permission ─────────────────────────
locals {
  routes = {
    "POST /predict"   = { arn=var.predict_lambda_invoke_arn,  name=var.predict_lambda_name }
    "GET /accuracy"   = { arn=var.accuracy_lambda_invoke_arn, name=var.accuracy_lambda_name }
    "POST /simulate"  = { arn=var.simulate_lambda_invoke_arn, name=var.simulate_lambda_name }
  }
}

resource "aws_apigatewayv2_integration" "predict" {
  api_id = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri = var.predict_lambda_invoke_arn
  payload_format_version = "2.0"
}
resource "aws_apigatewayv2_route" "predict" {
  api_id = aws_apigatewayv2_api.main.id
  route_key = "POST /predict"
  target = "integrations/${aws_apigatewayv2_integration.predict.id}"
}
resource "aws_lambda_permission" "predict" {
  statement_id = "AllowAPIPredict"
  action = "lambda:InvokeFunction"
  function_name = var.predict_lambda_name
  principal = "apigateway.amazonaws.com"
  source_arn = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_apigatewayv2_integration" "accuracy" {
  api_id = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri = var.accuracy_lambda_invoke_arn
  payload_format_version = "2.0"
}
resource "aws_apigatewayv2_route" "accuracy" {
  api_id = aws_apigatewayv2_api.main.id
  route_key = "GET /accuracy"
  target = "integrations/${aws_apigatewayv2_integration.accuracy.id}"
}
resource "aws_lambda_permission" "accuracy" {
  statement_id = "AllowAPIAccuracy"
  action = "lambda:InvokeFunction"
  function_name = var.accuracy_lambda_name
  principal = "apigateway.amazonaws.com"
  source_arn = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_apigatewayv2_integration" "simulate" {
  api_id = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri = var.simulate_lambda_invoke_arn
  payload_format_version = "2.0"
}
resource "aws_apigatewayv2_route" "simulate" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /simulate"
  target    = "integrations/${aws_apigatewayv2_integration.simulate.id}"
}
resource "aws_lambda_permission" "simulate" {
  statement_id = "AllowAPISimulate"
  action = "lambda:InvokeFunction"
  function_name = var.simulate_lambda_name
  principal = "apigateway.amazonaws.com"
  source_arn = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

output "api_url"          { value = aws_apigatewayv2_stage.default.invoke_url }
output "predict_endpoint" { value = "${aws_apigatewayv2_stage.default.invoke_url}/predict" }
output "accuracy_endpoint"{ value = "${aws_apigatewayv2_stage.default.invoke_url}/accuracy" }
output "simulate_endpoint"{ value = "${aws_apigatewayv2_stage.default.invoke_url}/simulate" }
