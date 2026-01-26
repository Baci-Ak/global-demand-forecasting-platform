/*
  File: outputs.tf

  Purpose:
  - Export identifiers for other modules/workloads (e.g., CI/CD, warehouse access).
*/

output "bucket_name" {
  description = "Bronze bucket name."
  value       = aws_s3_bucket.this.bucket
}

output "bucket_arn" {
  description = "Bronze bucket ARN."
  value       = aws_s3_bucket.this.arn
}
