# ==============================================================================
# envs/dev/rds-postgres/providers.tf
# ==============================================================================
#
# Purpose
# - Configure the Terraform backend and AWS provider for the dev RDS Postgres stack.
# - Remote state is stored in S3 with DynamoDB state locking enabled.
# ==============================================================================

terraform {
  backend "s3" {
    bucket         = "gdf-dev-tfstate-f6df28"
    key            = "envs/dev/rds-postgres/terraform.tfstate"
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
      component   = "rds-postgres"
    }
  }
}
