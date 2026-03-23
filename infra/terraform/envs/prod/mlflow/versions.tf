# ==============================================================================
# envs/prod/mlflow/versions.tf
# ==============================================================================
#
# Purpose
# - Pin Terraform and AWS provider versions for the prod MLflow stack.
# ==============================================================================

terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}