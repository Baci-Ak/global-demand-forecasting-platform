# ==============================================================================
# bootstrap/tfstate/providers.tf
# ==============================================================================
#
# Purpose
# - Configure the AWS provider for the bootstrap remote state stack.
# - Default tags enforce consistent tagging across resources.
#
# Notes
# - Authentication uses the AWS credential chain (AWS_PROFILE, env vars, SSO,
#   or IAM role in CI). Credentials are never hardcoded.
# ==============================================================================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      project     = var.project_name
      environment = var.environment
      managed_by  = "terraform"
      component   = "tfstate"
    }
  }
}
