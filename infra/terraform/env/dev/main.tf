/*
  File: env/dev/main.tf

  Purpose:
  - Environment entrypoint for dev.
  - This file should stay minimal:
    - Set env-specific variables
    - Call modules (added later)

  Next steps (not in this instruction):
  - Add modules for S3 bronze bucket, IAM, and cost guardrails (Budgets).
*/

terraform {
  # Backend configuration will be added once we decide remote state (S3 + DynamoDB).
  # For now, local state is acceptable for bootstrapping.
}




/*
  Dev environment entrypoint.

  This environment creates only the Bronze bucket first.
  Next resources (later steps): IAM roles/policies, Budgets, RDS for audit DB, etc.
*/

module "bronze_bucket" {
  source = "../../modules/s3_bronze"

  bucket_name    = "${var.project_name}-bronze-${var.environment}"
  retention_days = var.bronze_retention_days
}



module "dev_budget" {
  source = "../../modules/budgets"

  budget_name  = "${var.project_name}-${var.environment}-monthly-budget"
  limit_usd    = var.monthly_budget_limit_usd
  alert_emails = var.budget_alert_emails
}



module "github_actions_role" {
  source = "../../modules/github_oidc_role"

  role_name   = "${var.project_name}-github-actions-${var.environment}"
  github_org  = "Baci-Ak"
  github_repo = "global-demand-forecasting"
}


output "github_actions_role_arn" {
  description = "IAM role ARN assumed by GitHub Actions via OIDC (dev)."
  value       = module.github_actions_role.role_arn
}
