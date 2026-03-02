# ==============================================================================
# envs/dev/mwaa/providers.tf
# ==============================================================================
#
# Purpose
# - Configure the Terraform backend and AWS provider for the dev MWAA stack.
# ==============================================================================

terraform {
  backend "s3" {
    bucket         = "gdf-dev-tfstate-f6df28"
    key            = "envs/dev/mwaa/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "gdf-dev-terraform-locks"
    encrypt        = true
  }
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
