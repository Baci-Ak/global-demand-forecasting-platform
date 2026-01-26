/*
  File: versions.tf

  Purpose:
  - Pin Terraform and provider versions for repeatable, production-grade deployments.

  Why this matters:
  - Prevents "it worked yesterday" drift when teammates or CI run Terraform with different versions.
*/

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}
