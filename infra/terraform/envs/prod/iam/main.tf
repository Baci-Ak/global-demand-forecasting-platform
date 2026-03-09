# ==============================================================================
# envs/prod/iam/main.tf
# ==============================================================================
#
# Purpose
# - Root IAM stack for shared, environment-level IAM resources.
# - This stack owns reusable IAM roles and policies that other stacks can reference.
# ==============================================================================

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "terraform_execution" {
  name = "${var.project_name}-${var.environment}-terraform-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-terraform-exec"
  }
}



# ==============================================================================
# CI/CD role for GitHub Actions (prod)
# ==============================================================================

module "github_actions_ci_role" {
  source = "../../../modules/ci-federated-role"

  role_name = "${var.project_name}-${var.environment}-github-actions"

  # OIDC configuration
  oidc_provider_arn = var.github_oidc_provider_arn
  oidc_audience     = var.github_oidc_audience

  oidc_subjects = [
    "repo:${var.github_repo_owner}/${var.github_repo_name}:environment:${var.github_environment_name}"
  ]

  # MWAA environment permissions
  mwaa_environment_arn = "arn:aws:airflow:${var.aws_region}:*:environment/${var.project_name}-${var.environment}-mwaa"

  mwaa_execution_role_arn = "arn:aws:iam::*:role/${var.project_name}-${var.environment}-mwaa-execution-role"

  # Terraform backend locking
  terraform_lock_table_arn = "arn:aws:dynamodb:${var.aws_region}:*:table/${var.project_name}-${var.environment}-terraform-locks"

  # CloudWatch log groups for MWAA
  cloudwatch_log_group_prefix = "arn:aws:logs:${var.aws_region}:*:log-group:airflow-${var.project_name}-${var.environment}-mwaa-"

  tags = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
    component   = "ci-cd"
  }
}