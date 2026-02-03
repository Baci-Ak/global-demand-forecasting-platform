# ==============================================================================
# modules/s3/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose key attributes of the S3 bucket for consumption by other stacks.
# ==============================================================================

output "bucket_name" {
  description = "Name of the created S3 bucket."
  value       = aws_s3_bucket.this.bucket
}

output "bucket_arn" {
  description = "ARN of the created S3 bucket."
  value       = aws_s3_bucket.this.arn
}
