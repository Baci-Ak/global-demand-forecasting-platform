# ==============================================================================
# modules/rds-postgres/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose identifiers needed by callers to attach rules and provision the DB.
# ==============================================================================

output "db_subnet_group_name" {
  description = "Name of the DB subnet group."
  value       = aws_db_subnet_group.this.name
}

output "db_security_group_id" {
  description = "Security group ID for the Postgres database."
  value       = aws_security_group.db.id
}



output "endpoint" {
  description = "RDS endpoint hostname."
  value       = aws_db_instance.this.address
}

output "port" {
  description = "RDS port."
  value       = aws_db_instance.this.port
}

output "db_name" {
  description = "Database name."
  value       = aws_db_instance.this.db_name
}


output "db_instance_identifier" {
  description = "RDS DB instance identifier (DBInstanceIdentifier)."
  value       = aws_db_instance.this.id
}