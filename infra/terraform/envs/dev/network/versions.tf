# ==============================================================================
# envs/dev/network/versions.tf
# ==============================================================================
#
# Purpose
# - Pin Terraform and provider versions for repeatable infrastructure builds.
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
