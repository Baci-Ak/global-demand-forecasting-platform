# ==============================================================================
# envs/prod/iam/github_oidc_provider.tf
# ==============================================================================
#
# Purpose
# - Create the GitHub Actions OIDC provider in the current AWS account.
# - This is required so GitHub Actions can assume the prod CI/CD role via OIDC.
#
# Notes
# - The provider must exist in the same AWS account as the IAM role being assumed.
# - The old account-specific ARN in terraform.tfvars is no longer valid after the
#   AWS account switch.
# ==============================================================================

resource "aws_iam_openid_connect_provider" "github_actions" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com"
  ]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1"
  ]

  tags = {
    Name        = "${var.project_name}-${var.environment}-github-actions-oidc"
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
    component   = "ci-cd"
  }
}