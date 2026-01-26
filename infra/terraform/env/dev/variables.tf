/*
  File: env/dev/variables.tf

  Purpose:
  - Declare variables used by the dev root module.
  - Terraform only loads *.tf files within the current working directory,
    so variables declared in parent folders are not visible here.

  Source of truth:
  - The canonical definitions live in infra/terraform/variables.tf.
  - We mirror declarations here so env/dev can be executed independently.
*/

variable "project_name" {
  description = "Short project identifier used for naming and tagging."
  type        = string
  default     = "global-demand-forecasting"
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod)."
  type        = string
}

variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}



variable "bronze_retention_days" {
  description = "Days to retain Bronze objects before lifecycle expiration."
  type        = number
  default     = 180
}




variable "monthly_budget_limit_usd" {
  description = "Monthly AWS cost budget limit (USD) for dev."
  type        = number
  default     = 25
}

variable "budget_alert_emails" {
  description = "Email addresses to notify when budget thresholds are crossed."
  type        = list(string)
  default     = []
}

