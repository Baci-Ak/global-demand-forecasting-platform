# ==============================================================================
# envs/dev/redshift/outputs.tf
# ==============================================================================
#
# Purpose
# - Export Redshift connection details and the admin secret reference.
# ==============================================================================

output "namespace_name" {
  description = "Redshift Serverless namespace name."
  value       = module.redshift.namespace_name
}

output "workgroup_name" {
  description = "Redshift Serverless workgroup name."
  value       = module.redshift.workgroup_name
}

output "endpoint" {
  description = "Redshift Serverless endpoint address."
  value       = module.redshift.endpoint_address
}

output "port" {
  description = "Redshift Serverless endpoint port."
  value       = module.redshift.endpoint_port
}

output "admin_secret_arn" {
  description = "Secrets Manager secret ARN for Redshift admin credentials."
  value       = aws_secretsmanager_secret.redshift_admin.arn
}

output "redshift_security_group_id" {
  description = "Security group id attached to the Redshift workgroup."
  value       = module.redshift.security_group_id
}
