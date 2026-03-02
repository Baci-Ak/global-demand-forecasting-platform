# ==============================================================================
# envs/dev/redshift/versions.tf
# ==============================================================================
#
# Purpose
# - Define Terraform and provider version constraints for the dev Redshift stack.
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
