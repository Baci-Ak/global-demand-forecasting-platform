# ==============================================================================
# bootstrap/tfstate/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose backend identifiers used when configuring remote state in other stacks.
# ==============================================================================

output "tfstate_bucket_name" {
  description = "S3 bucket name for Terraform remote state."
  value       = aws_s3_bucket.tfstate.bucket
}

output "tf_locks_table_name" {
  description = "DynamoDB table name for Terraform state locking."
  value       = aws_dynamodb_table.tf_locks.name
}
