/*
  Module: github_oidc_role

  Purpose:
  - Create an IAM role assumable by GitHub Actions via OIDC
  - No long-lived AWS credentials
  - Repo-scoped trust (least privilege)
*/

variable "role_name" {
  description = "Name of the IAM role to create."
  type        = string
}

variable "github_org" {
  description = "GitHub organization or username."
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name."
  type        = string
}
