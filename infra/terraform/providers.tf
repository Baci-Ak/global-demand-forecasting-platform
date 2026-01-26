/*
  File: providers.tf

  Purpose:
  - Configure cloud providers used by this project.

  Notes:
  - Authentication is handled outside Terraform (recommended):
    - AWS_PROFILE (SSO) or environment variables, etc.
  - Do NOT hardcode credentials here.
*/

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      project     = var.project_name
      environment = var.environment
      managed_by  = "terraform"
    }
  }
}
