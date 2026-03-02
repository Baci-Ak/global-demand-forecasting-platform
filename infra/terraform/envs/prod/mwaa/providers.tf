# ==============================================================================
# envs/dev/mwaa/providers.tf
# ==============================================================================
#
# Purpose
# - Configure the Terraform backend and AWS provider for the dev MWAA stack.
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
      component   = "mwaa"
    }
  }
}
