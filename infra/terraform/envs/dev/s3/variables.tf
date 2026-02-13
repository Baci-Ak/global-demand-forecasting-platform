# ==============================================================================
# envs/dev/s3/variables.tf
# ==============================================================================
#
# Purpose
# - Inputs for the dev S3 stack.
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
}

variable "enable_versioning" {
  description = "Whether to enable S3 bucket versioning for the dev bronze bucket."
  type        = bool
  default     = true
}

variable "s3_bucket_tags" {
  description = "Additional tags to apply to the dev bronze bucket."
  type        = map(string)
  default     = {}
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
  default     = true
}
