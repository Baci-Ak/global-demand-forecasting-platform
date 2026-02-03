# ==============================================================================
# modules/s3/variables.tf
# ==============================================================================
#
# Purpose
# - Declare inputs for the reusable S3 module.
# - Keep inputs small, stable, and explicit to avoid hidden coupling.
# ==============================================================================

variable "bucket_name" {
  description = "Name of the S3 bucket to create. Must be globally unique."
  type        = string
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
