# ==============================================================================
# envs/dev/redshift/terraform.tfvars
# ==============================================================================
#
# Purpose
# - Environment inputs for the dev Redshift Serverless stack.
# - Values here should be safe to commit (no secrets).
# ==============================================================================

# ------------------------------------------------------------------------------
# Global environment identity
# ------------------------------------------------------------------------------

project_name = "gdf"
environment  = "prod"
aws_region   = "us-east-1"

# ------------------------------------------------------------------------------
# Warehouse identity (dev)
# ------------------------------------------------------------------------------

database_name  = "warehouse"
admin_username = "admin"

# ------------------------------------------------------------------------------
# Redshift Serverless configuration (dev)
# ------------------------------------------------------------------------------

# Base capacity is in RPUs. Keep small in dev; scale up when needed.
base_capacity = 8

# Default Redshift port
port = 5439


#Redshift Serverless usage limits (cost cap)
enable_usage_limits = true

# Dev: start with a monthly cap to prevent surprises.
usage_limit_rpu_hours_per_day   = null
usage_limit_rpu_hours_per_week  = null
usage_limit_rpu_hours_per_month = 200

# Dev: log only (don’t hard-stop dev)
usage_limit_breach_action = "log"


enable_log_exports = true