# ==============================================================================
# envs/dev/rds-postgres/terraform.tfvars
# ==============================================================================
#
# Purpose
# - Environment inputs for the dev RDS Postgres stack.
# - Values here should be safe to commit (no secrets).
# ==============================================================================

# ------------------------------------------------------------------------------
# Global environment identity
# ------------------------------------------------------------------------------

project_name = "gdf"
environment  = "dev"
aws_region   = "us-east-1"

# ------------------------------------------------------------------------------
# Database identity (dev)
# ------------------------------------------------------------------------------

db_name     = "gdf_audit"
db_username = "gdf_admin"

# ------------------------------------------------------------------------------
# RDS configuration (dev)
# ------------------------------------------------------------------------------

engine_version        = "16.3"
instance_class        = "db.t4g.micro"
allocated_storage_gb  = 20
backup_retention_days = 7
publicly_accessible   = false
deletion_protection   = false
skip_final_snapshot   = true
db_port               = 5432




multi_az                 = false
max_allocated_storage_gb = 0

performance_insights_enabled          = false
performance_insights_retention_period = 7

monitoring_interval_seconds = 0