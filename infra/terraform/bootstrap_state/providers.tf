/*
  Providers for bootstrap stack.

  Important:
  - Do NOT hardcode credentials.
  - Use AWS_PROFILE / SSO / env vars on your machine.
*/

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      project     = var.project_name
      environment = var.environment
      managed_by  = "terraform"
      component   = "bootstrap_state"
    }
  }
}
