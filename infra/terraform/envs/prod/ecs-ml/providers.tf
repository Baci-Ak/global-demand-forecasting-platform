# ==============================================================================
# envs/prod/ecs-ml/providers.tf
# ==============================================================================
#
# Purpose
# - Configure the Terraform backend and AWS provider for the prod ECS ML stack.
# - Align with the existing prod stack pattern.
# ==============================================================================

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
      component   = "ecs-ml-runtime"
    }
  }
}