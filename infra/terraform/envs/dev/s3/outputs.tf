# ==============================================================================
# envs/dev/s3/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose stack-level outputs for integration with other stacks.
# - These outputs are typically consumed via terraform_remote_state or CI/CD.
# ==============================================================================

output "bronze_bucket_name" {
  description = "Name of the dev bronze bucket."
  value       = module.bronze_bucket.bucket_name
}

output "bronze_bucket_arn" {
  description = "ARN of the dev bronze bucket."
  value       = module.bronze_bucket.bucket_arn
}

output "bronze_bucket_id" {
  description = "ID of the dev bronze bucket."
  value       = module.bronze_bucket.bucket_id
}


output "iam_terraform_execution_role_arn" {
  description = "IAM stack terraform execution role ARN (from remote state)."
  value       = data.terraform_remote_state.iam.outputs.terraform_execution_role_arn
}
