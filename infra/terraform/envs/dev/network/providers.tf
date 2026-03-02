# ==============================================================================
# envs/dev/network/providers.tf
# ==============================================================================
#
# Purpose
# - Configure the Terraform backend and AWS provider for the dev network stack.
# - Remote state is stored in S3 with DynamoDB state locking enabled.
# ==============================================================================

terraform {
  backend "s3" {
    bucket         = "gdf-dev-tfstate-f6df28"
    key            = "envs/dev/network/terraform.tfstate"
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
      component   = "network"
    }
  }
}
