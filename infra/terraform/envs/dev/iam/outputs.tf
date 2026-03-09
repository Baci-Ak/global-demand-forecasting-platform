# ==============================================================================
# envs/dev/iam/outputs.tf
# ==============================================================================
#
# Purpose
# - Export IAM resources for consumption by other stacks via remote state.
# ==============================================================================

output "terraform_execution_role_name" {
  description = "Name of the shared Terraform execution role."
  value       = aws_iam_role.terraform_execution.name
}

output "terraform_execution_role_arn" {
  description = "ARN of the shared Terraform execution role."
  value       = aws_iam_role.terraform_execution.arn
}

output "account_id" {
  description = "AWS account id for this environment."
  value       = data.aws_caller_identity.current.account_id
}



# ------------------------------------------------------------------------------
# CI/CD role outputs
# ------------------------------------------------------------------------------
output "github_actions_role_name" {
  description = "Name of the GitHub Actions federated IAM role for this environment."
  value       = module.github_actions_ci_role.role_name
}

output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions federated IAM role for this environment."
  value       = module.github_actions_ci_role.role_arn
}