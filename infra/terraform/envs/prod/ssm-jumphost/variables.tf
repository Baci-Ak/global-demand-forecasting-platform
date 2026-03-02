# ==============================================================================
# envs/dev/ssm-jumphost/variables.tf
# ==============================================================================
#
# Purpose
# - Inputs for the dev SSM jump host stack.
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
