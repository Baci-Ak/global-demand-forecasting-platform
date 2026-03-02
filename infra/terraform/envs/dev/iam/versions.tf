# ==============================================================================
# envs/dev/iam/versions.tf
# ==============================================================================
#
# Purpose
# - Define Terraform and provider version constraints for the dev IAM stack.
#
# Notes
# - Keeping versions pinned ensures reproducible infrastructure builds.
# ==============================================================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
