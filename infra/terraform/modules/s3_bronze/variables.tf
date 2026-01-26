/*
  Module: s3_bronze

  Purpose:
  - Provision the Bronze S3 bucket used as the raw landing zone for ingested data.

  Production-grade defaults:
  - Block all public access
  - Enable versioning
  - Enable server-side encryption (SSE-S3)
  - Add lifecycle rules to control storage costs
*/

variable "bucket_name" {
  description = "Name of the Bronze S3 bucket."
  type        = string
}

variable "retention_days" {
  description = "Number of days to retain objects before expiring them (cost guardrail)."
  type        = number
  default     = 180
}
