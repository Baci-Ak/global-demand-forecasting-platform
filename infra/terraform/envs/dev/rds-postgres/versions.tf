# ==============================================================================
# envs/dev/rds-postgres/versions.tf
# ==============================================================================
#
# Purpose
# - Pin Terraform and provider versions for repeatable infrastructure builds.
# - Version pinning prevents unexpected breaking changes during upgrades.
# ==============================================================================


terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

