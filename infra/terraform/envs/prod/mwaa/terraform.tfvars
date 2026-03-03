# ==============================================================================
# envs/prod/mwaa/terraform.tfvars
# ==============================================================================
#
# Purpose
# - Environment inputs for the prod MWAA stack.
# - Values here should be safe to commit (no secrets).
# ==============================================================================

# ------------------------------------------------------------------------------
# Global environment identity
# ------------------------------------------------------------------------------
project_name = "gdf"
environment  = "prod"
aws_region   = "us-east-1"

# ------------------------------------------------------------------------------
# MWAA configuration (prod)
# ------------------------------------------------------------------------------
airflow_version        = "2.8.1"
environment_class      = "mw1.medium"
min_workers            = 1
max_workers            = 2
webserver_access_mode  = "PRIVATE_ONLY"

# ------------------------------------------------------------------------------
# DAG storage
# ------------------------------------------------------------------------------
dag_s3_bucket = "gdf-prod-airflow"
dag_s3_path   = "airflow/dags"

# ------------------------------------------------------------------------------
# Webserver access controls
# ------------------------------------------------------------------------------
# PRIVATE_ONLY: access is via VPC (SSM/jumphost/VPN), not public CIDRs.
webserver_ingress_port     = 443
webserver_ingress_protocol = "tcp"
enable_egress_all          = true

# ------------------------------------------------------------------------------
# Optional MWAA artifacts (relative to the source bucket)
# ------------------------------------------------------------------------------
requirements_s3_path   = "airflow/requirements/requirements.txt"
plugins_s3_path        = "airflow/plugins/plugins.zip"
startup_script_s3_path = "airflow/startup/startup.sh"

# ------------------------------------------------------------------------------
# Airflow config overrides
# ------------------------------------------------------------------------------
airflow_configuration_options = {
  "core.load_examples"              = "False"
  "webserver.warn_deployment_exposure" = "False"
}

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
logging_configuration = {
  dag_processing = { enabled = true, log_level = "INFO" }
  scheduler      = { enabled = true, log_level = "INFO" }
  task           = { enabled = true, log_level = "INFO" }
  webserver      = { enabled = true, log_level = "INFO" }
  worker         = { enabled = true, log_level = "INFO" }
}

cloudwatch_log_retention_days = 3