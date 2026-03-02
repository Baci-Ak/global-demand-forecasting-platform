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

terraform {
  backend "s3" {
    bucket         = "gdf-dev-tfstate-f6df28"
    key            = "envs/dev/s3/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "gdf-dev-terraform-locks"
    encrypt        = true
  }
}

data "terraform_remote_state" "iam" {
  backend = "s3"

  config = {
    bucket       = "gdf-dev-tfstate-f6df28"
    key          = "envs/dev/iam/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
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
