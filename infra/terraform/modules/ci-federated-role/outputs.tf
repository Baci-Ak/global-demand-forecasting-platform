# ==============================================================================
# modules/ci-federated-role/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose the created CI/CD federated role identity for environment stacks and
#   GitHub configuration.
# ==============================================================================

output "role_name" {
  description = "Name of the CI/CD federated IAM role."
  value       = aws_iam_role.this.name
}

output "role_arn" {
  description = "ARN of the CI/CD federated IAM role."
  value       = aws_iam_role.this.arn
}