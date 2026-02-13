# ==============================================================================
# modules/s3/variables.tf
# ==============================================================================
#
# Purpose
# - Declare inputs for the reusable S3 module.
# - Keep inputs explicit to make the module easy to understand and adopt.
#
# Notes
# - Bucket names must be globally unique across AWS.
# - KMS key ARN is only required when sse_algorithm is "aws:kms".
# ==============================================================================

variable "project_name" {
  description = "Project identifier used for tagging and resource naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment name (dev/prod)."
  type        = string
}

variable "bucket_name" {
  description = "Name of the S3 bucket to create. Must be globally unique."
  type        = string

  validation {
    condition     = length(var.bucket_name) >= 3 && length(var.bucket_name) <= 63
    error_message = "bucket_name must be between 3 and 63 characters."
  }
}

variable "enable_versioning" {
  description = "Whether to enable S3 bucket versioning."
  type        = bool
  default     = true
}

variable "force_destroy" {
  description = "Whether Terraform is allowed to destroy the bucket even if it contains objects."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags to apply to the bucket."
  type        = map(string)
  default     = {}
}

variable "sse_algorithm" {
  description = "Server-side encryption algorithm for the bucket. Use AES256 (SSE-S3) or aws:kms (SSE-KMS)."
  type        = string
  default     = "AES256"

  validation {
    condition     = contains(["AES256", "aws:kms"], var.sse_algorithm)
    error_message = "sse_algorithm must be either \"AES256\" (SSE-S3) or \"aws:kms\" (SSE-KMS)."
  }
}

variable "kms_key_arn" {
  description = "KMS key ARN used when sse_algorithm is aws:kms. Leave null for SSE-S3."
  type        = string
  default     = null

  validation {
    condition     = var.sse_algorithm != "aws:kms" || (var.kms_key_arn != null && trim(var.kms_key_arn) != "")
    error_message = "kms_key_arn must be set when sse_algorithm is \"aws:kms\"."
  }
}
