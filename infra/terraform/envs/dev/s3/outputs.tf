# ==============================================================================
# envs/dev/s3/outputs.tf
# ==============================================================================
#
# Purpose
# - Root module outputs for the dev S3 stack.
# - Re-exposes key module outputs for humans and for other automation.
# ==============================================================================

output "bronze_bucket_name" {
  description = "Name of the dev bronze S3 bucket."
  value       = module.bronze_bucket.bucket_name
}

output "bronze_bucket_arn" {
  description = "ARN of the dev bronze S3 bucket."
  value       = module.bronze_bucket.bucket_arn
}



output "artifacts_bucket_name" {
  description = "Name of the dev artifacts S3 bucket."
  value       = module.artifacts_bucket.bucket_name
}

output "artifacts_bucket_arn" {
  description = "ARN of the dev artifacts S3 bucket."
  value       = module.artifacts_bucket.bucket_arn
}
