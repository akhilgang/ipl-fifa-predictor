variable "project_name"   { type = string }
variable "api_gateway_url" { type = string }
variable "github_repo"     { type = string }
# variable "github_token" {
#   type      = string
#   sensitive = true
# }
variable "branch" {
  type    = string
  default = "main"
}

resource "aws_amplify_app" "ui" {
  name         = "${var.project_name}-ui"
  repository   = var.github_repo
  # access_token = var.github_token

  # Amplify reads amplify.yml from repo root — no build_spec needed here
  build_spec = null

  environment_variables = {
    REACT_APP_API_URL      = var.api_gateway_url
    REACT_APP_PROJECT_NAME = var.project_name
    _LIVE_UPDATES = jsonencode([{
      pkg     = "node"
      type    = "nvm"
      version = "18"
    }])
  }

  # SPA: serve index.html for all non-asset routes
  custom_rule {
    source = "</^[^.]+$|\\.(?!(css|gif|ico|jpg|js|png|txt|svg|woff|woff2|ttf|map|json)$)([^.]+$)/>"
    status = "200"
    target = "/index.html"
  }

  tags = { Project = var.project_name }
}

resource "aws_amplify_branch" "main" {
  app_id      = aws_amplify_app.ui.id
  branch_name = var.branch
  stage       = "PRODUCTION"
  framework   = "React"

  enable_auto_build           = false
  enable_pull_request_preview = true

  environment_variables = {
    REACT_APP_API_URL = var.api_gateway_url
  }
}

output "app_url"    { value = "https://${var.branch}.${aws_amplify_app.ui.default_domain}" }
output "app_id"     { value = aws_amplify_app.ui.id }
output "app_domain" { value = aws_amplify_app.ui.default_domain }
