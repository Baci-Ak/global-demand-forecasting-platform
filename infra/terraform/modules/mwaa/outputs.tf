# ==============================================================================
# modules/mwaa/outputs.tf
# ==============================================================================
#
# Purpose
# - Export MWAA environment details.
# ==============================================================================

output "environment_name" {
  description = "MWAA environment name."
  value       = aws_mwaa_environment.this.name
}

output "webserver_url" {
  description = "MWAA webserver URL."
  value       = aws_mwaa_environment.this.webserver_url
}

output "execution_role_arn" {
  description = "MWAA execution role ARN."
  value       = aws_iam_role.mwaa_execution.arn
}

output "security_group_id" {
  description = "Security group id attached to MWAA."
  value       = aws_security_group.mwaa.id
}
