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
  default = ""
}

variable "github_token" {
  type      = string
  default   = ""
  sensitive = true
}

# variable "football_data_api_key" {
#   type      = string
#   default   = ""
#   sensitive = true
# }

# variable "cricbuzz_api_key" {
#   type      = string
#   default   = ""
#   sensitive = true
# }

variable "alert_email" {
  type    = string
  default = "ubitosan22@email.com"
}
