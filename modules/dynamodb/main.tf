variable "project_name" { type = string }

locals {
  tables = {
    ipl_predictions  = { hash="match_id", range="timestamp" }
    ipl_stats        = { hash="stat_key",  range=null }
    fifa_predictions = { hash="match_id", range="timestamp" }
    fifa_stats       = { hash="stat_key",  range=null }
  }
}

resource "aws_dynamodb_table" "ipl_predictions" {
  name         = "${var.project_name}-ipl-predictions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "match_id"
  range_key    = "timestamp"
  attribute {
    name = "match_id"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "S"
  }
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
  tags = { Project = var.project_name, Sport = "IPL" }
}

resource "aws_dynamodb_table" "ipl_stats" {
  name         = "${var.project_name}-ipl-stats"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "stat_key"
  attribute {
    name = "stat_key"
    type = "S"
  }
  tags = { Project=var.project_name, Sport="IPL" }
}

resource "aws_dynamodb_table" "fifa_predictions" {
  name         = "${var.project_name}-fifa-predictions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "match_id"
  range_key    = "timestamp"
  attribute {
    name = "match_id"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "S"
  }
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
  tags = { Project = var.project_name, Sport = "FIFA" }
}

resource "aws_dynamodb_table" "fifa_stats" {
  name         = "${var.project_name}-fifa-stats"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "stat_key"
  attribute {
    name = "stat_key"
    type = "S"
  }
  tags = { Project=var.project_name, Sport="FIFA" }
}

output "ipl_predictions_table_name"  { value = aws_dynamodb_table.ipl_predictions.name }
output "ipl_stats_table_name"        { value = aws_dynamodb_table.ipl_stats.name }
output "fifa_predictions_table_name" { value = aws_dynamodb_table.fifa_predictions.name }
output "fifa_stats_table_name"       { value = aws_dynamodb_table.fifa_stats.name }

output "all_table_arns" { value = [
  aws_dynamodb_table.ipl_predictions.arn,
  aws_dynamodb_table.ipl_stats.arn,
  aws_dynamodb_table.fifa_predictions.arn,
  aws_dynamodb_table.fifa_stats.arn,
]}
