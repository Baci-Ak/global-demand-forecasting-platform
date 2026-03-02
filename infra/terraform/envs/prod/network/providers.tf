# ==============================================================================
# envs/dev/network/providers.tf
# ==============================================================================
#
# Purpose
# - Configure the Terraform backend and AWS provider for the dev network stack.
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
      component   = "network"
    }
  }
}
