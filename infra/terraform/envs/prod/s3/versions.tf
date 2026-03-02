# ==============================================================================
# envs/dev/_global/versions.tf
# ==============================================================================
#
# Purpose
# - Pin Terraform and provider versions for the dev environment.
# - Keeps builds deterministic and reduces drift across machines and CI.
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
