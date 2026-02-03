# ==============================================================================
# envs/dev/_global/providers.tf
# ==============================================================================
#
# Purpose
# - Configure the AWS provider for the dev environment.
# - Default tags enforce consistent tagging across all resources.
#
# Notes
# - Authentication uses the AWS credential chain (AWS_PROFILE, env vars, SSO,
#   or IAM role in CI). Provider config does not hardcode credentials.
# ==============================================================================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      project     = var.project_name
      environment = var.environment
      managed_by  = "terraform"
    }
  }
}
