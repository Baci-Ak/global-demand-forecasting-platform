# ==============================================================================
# envs/dev/iam/variables.tf
# ==============================================================================
#
# Purpose
# - Inputs for the dev IAM stack.
# - Values are set via terraform.tfvars (no secrets).
# ==============================================================================

variable "project_name" {
  description = "Project identifier used for tagging and resource naming."
  type        = string
  default     = "gdf"
}

variable "environment" {
  description = "Deployment environment name (dev/prod)."
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for all resources in this environment."
  type        = string
  default     = "us-east-1"
}



# ------------------------------------------------------------------------------
# CI/CD federated role inputs
# ------------------------------------------------------------------------------
#variable "github_oidc_provider_arn" {
  #description = "ARN of the GitHub Actions OIDC provider."
  #type        = string
#}

variable "github_oidc_audience" {
  description = "Audience expected in GitHub OIDC tokens."
  type        = string
  default     = "sts.amazonaws.com"
}

variable "github_repo_owner" {
  description = "GitHub repository owner/org for OIDC subject matching."
  type        = string
}

variable "github_repo_name" {
  description = "GitHub repository name for OIDC subject matching."
  type        = string
}

variable "github_environment_name" {
  description = "GitHub Actions environment name allowed to assume this role."
  type        = string
}