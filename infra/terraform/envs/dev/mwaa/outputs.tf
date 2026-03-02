# ==============================================================================
# envs/dev/mwaa/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose MWAA environment outputs for operators and downstream stacks.
# ==============================================================================

output "mwaa_environment_name" {
  description = "MWAA environment name."
  value       = module.mwaa.environment_name
}

output "mwaa_webserver_url" {
  description = "MWAA webserver URL."
  value       = module.mwaa.webserver_url
}

output "mwaa_execution_role_arn" {
  description = "MWAA execution role ARN."
  value       = module.mwaa.execution_role_arn
}

output "mwaa_security_group_id" {
  description = "Security group id attached to MWAA."
  value       = module.mwaa.security_group_id
}
