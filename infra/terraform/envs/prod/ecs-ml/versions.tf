# ==============================================================================
# envs/prod/ecs-ml/versions.tf
# ==============================================================================
#
# Purpose
# - Pin Terraform and AWS provider versions for the ECS ML runtime stack.
# - Keeps infrastructure deployments deterministic across engineers and CI.
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