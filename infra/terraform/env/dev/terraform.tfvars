/*
  File: terraform.tfvars.example

  Purpose:
  - Example values for local development.
  - Copy to terraform.tfvars (which must NOT be committed) and adjust as needed.
*/

environment = "dev"
aws_region  = "us-east-1"
bronze_retention_days = 180


monthly_budget_limit_usd = 25
budget_alert_emails      = ["bassi.cim@gmail.com"]
