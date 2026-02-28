# ==============================================================================
# modules/rds-postgres/db.tf
# ==============================================================================
#
# Purpose
# - Provision a managed Postgres database instance for audit logging.
#
# Notes
# - Deployed into private subnets via the DB subnet group.
# - Not publicly accessible.
# - Storage encryption enabled by default.
# ==============================================================================

resource "aws_db_instance" "this" {
  identifier = "${var.project_name}-${var.environment}-audit-postgres"

  engine         = "postgres"
  engine_version = var.engine_version

  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage_gb
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.db_name
  username = var.master_username
  password = var.master_password
  port = var.db_port


  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.db.id]

  publicly_accessible = var.publicly_accessible

  backup_retention_period = var.backup_retention_days

  # Dev-safe defaults. For production, consider Multi-AZ and stricter snapshot behavior.
  deletion_protection = var.deletion_protection
  skip_final_snapshot = var.skip_final_snapshot

  # Minor version upgrades can be enabled in dev; review for production.
  auto_minor_version_upgrade = true

  multi_az = var.multi_az

  # Storage autoscaling (recommended in prod to avoid outages)
  max_allocated_storage = var.max_allocated_storage_gb > 0 ? var.max_allocated_storage_gb : null

  # Performance Insights (great for debugging; cost-aware defaults)
  performance_insights_enabled          = var.performance_insights_enabled
  performance_insights_retention_period = var.performance_insights_enabled ? var.performance_insights_retention_period : null

  # Enhanced monitoring (optional; cost-aware)
  monitoring_interval = var.monitoring_interval_seconds

  tags = {
    Name = "${var.project_name}-${var.environment}-audit-postgres"
  }
}
