# ==============================================================================
# envs/dev/iam/terraform.tfvars
# ==============================================================================
#
# Purpose
# - Dev IAM stack input values.
# - Keep backend values consistent across all dev stacks.
# ==============================================================================

project_name = "gdf"
environment  = "prod"
aws_region   = "us-east-1"



# ------------------------------------------------------------------------------
# GitHub Actions OIDC / CI-CD role
# ------------------------------------------------------------------------------
github_oidc_provider_arn = "arn:aws:iam::798329741238:oidc-provider/token.actions.githubusercontent.com"
github_oidc_audience     = "sts.amazonaws.com"
github_repo_owner        = "Baci-Ak"
github_repo_name         = "global-demand-forecasting"
github_environment_name  = "prod"