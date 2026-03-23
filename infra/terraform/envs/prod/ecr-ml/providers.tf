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

# ==============================================================================
# envs/dev/s3/providers.tf
# ==============================================================================
#
# Purpose
# - Configure the Terraform backend and AWS provider for the dev S3 stack.
# - Remote state is stored in S3 with DynamoDB state locking enabled.
# ==============================================================================


# run terraform init -reconfigure -backend-config=backend.hcl
terraform {
  backend "s3" {}
}




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
