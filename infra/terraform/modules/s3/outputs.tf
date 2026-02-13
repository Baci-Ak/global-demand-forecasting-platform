# ==============================================================================
# modules/s3/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose identifiers needed by other stacks (IAM, MWAA, Redshift, apps).
# ==============================================================================

output "bucket_name" {
  description = "S3 bucket name."
  value       = aws_s3_bucket.this.bucket
}

output "bucket_arn" {
  description = "S3 bucket ARN."
  value       = aws_s3_bucket.this.arn
}

output "bucket_id" {
  description = "S3 bucket ID."
  value       = aws_s3_bucket.this.id
}
