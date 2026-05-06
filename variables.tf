variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "project_name" {
  type    = string
  default = "sports-predictor"
}

variable "log_retention_days" {
  type    = number
  default = 7
}

variable "github_repo" {
  type    = string
  default = "https://github.com/akhilgang/ipl-fifa-predictor.git"
}

variable "github_token" {
  type      = string
  default   = "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"
  sensitive = true
}

variable "github_branch" {
  type    = string
  default = "new"
}

# variable "cricbuzz_api_key" {
#   type      = string
#   default   = ""
#   sensitive = true
# }

variable "alert_email" {
  type    = string
  default = "ubitosan22@email.com"
}
