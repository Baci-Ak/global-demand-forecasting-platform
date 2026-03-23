# ==============================================================================
# envs/dev/rds-postgres/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose dev RDS Postgres stack outputs for integration with other stacks/apps.
# ==============================================================================

output "db_subnet_group_name" {
  description = "DB subnet group name for the dev Postgres database."
  value       = module.rds_postgres.db_subnet_group_name
}

output "db_security_group_id" {
  description = "Security group ID for the dev Postgres database."
  value       = module.rds_postgres.db_security_group_id
}

output "endpoint" {
  description = "RDS endpoint hostname for the dev Postgres database."
  value       = module.rds_postgres.endpoint
}

output "port" {
  description = "RDS port for the dev Postgres database."
  value       = module.rds_postgres.port
}

output "db_name" {
  description = "Database name for the dev Postgres database."
  value       = module.rds_postgres.db_name
}




output "iam_terraform_execution_role_arn" {
  description = "IAM stack terraform execution role ARN (from remote state)."
  value       = data.terraform_remote_state.iam.outputs.terraform_execution_role_arn
}


output "db_instance_identifier" {
  description = "RDS DB instance identifier (DBInstanceIdentifier)."
  value       = module.rds_postgres.db_instance_identifier
}




