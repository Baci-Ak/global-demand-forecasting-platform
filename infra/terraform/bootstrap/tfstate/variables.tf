# ==============================================================================
# bootstrap/tfstate/variables.tf
# ==============================================================================
#
# Purpose
# - Declare inputs for the bootstrap remote state stack.
# - Values are safe to commit (no secrets).
# ==============================================================================

variable "project_name" {
  description = "Project identifier used for naming and tagging."
  type        = string
  default     = "gdf"
}

variable "environment" {
  description = "Deployment environment name (dev/prod)."
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region to deploy the remote state backend into."
  type        = string
  default     = "us-east-1"
}
