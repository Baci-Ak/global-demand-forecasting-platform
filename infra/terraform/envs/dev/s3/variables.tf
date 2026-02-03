# ==============================================================================
# envs/dev/_global/variables.tf
# ==============================================================================
#
# Purpose
# - Environment-wide variables shared across all dev stacks.
# - Values are set via terraform.tfvars or CI/CD, not hardcoded in modules.
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
}


variable "s3_sse_algorithm" {
  description = "Default server-side encryption algorithm for dev S3 buckets. AES256 (SSE-S3) or aws:kms (SSE-KMS)."
  type        = string
  default     = "AES256"

  validation {
    condition     = contains(["AES256", "aws:kms"], var.s3_sse_algorithm)
    error_message = "s3_sse_algorithm must be either \"AES256\" or \"aws:kms\"."
  }
}



variable "s3_force_destroy" {
  description = "Whether Terraform may delete objects when destroying dev buckets. Use with care."
  type        = bool
  default     = false
}
