# ==============================================================================
# envs/dev/mwaa/terraform.tfvars
# ==============================================================================
#
# Purpose
# - Environment inputs for the dev MWAA stack.
# - Values here should be safe to commit (no secrets).
# ==============================================================================

# ------------------------------------------------------------------------------
# Global environment identity
# ------------------------------------------------------------------------------

project_name = "gdf"
environment  = "prod"
aws_region   = "us-east-1"

# ------------------------------------------------------------------------------
# MWAA configuration (dev)
# ------------------------------------------------------------------------------

airflow_version   = "2.8.1"
environment_class = "mw1.medium"
min_workers       = 1
max_workers       = 2
# PUBLIC_ONLY for bublic or PRIVATE_ONLY for private
webserver_access_mode = "PRIVATE_ONLY"

# ------------------------------------------------------------------------------
# DAG storage
# ------------------------------------------------------------------------------

# Use an existing bucket (recommended: your artifacts bucket if you have one).
# If you only have the bronze bucket today, you can set this to "gdf-dev-bronze"
# and use a dedicated prefix like "airflow/dags".
dag_s3_bucket = "gdf-dev-airflow"
dag_s3_path   = "airflow/dags"



# ------------------------------------------------------------------------------
# Webserver access controls
# ------------------------------------------------------------------------------
# public CIDR: "37.203.155.52/32"
allowed_web_cidr_blocks    = ["37.203.155.52/32"]
webserver_ingress_port     = 443
webserver_ingress_protocol = "tcp"
enable_egress_all          = true

# ------------------------------------------------------------------------------
# Optional MWAA artifacts (relative to the source bucket)
# ------------------------------------------------------------------------------
#"airflow/requirements/requirements.txt"
requirements_s3_path   = "airflow/requirements/requirements.txt"
plugins_s3_path        = "airflow/plugins/plugins.zip"
startup_script_s3_path = "airflow/startup/startup.sh"


# ------------------------------------------------------------------------------
# Airflow config overrides
# ------------------------------------------------------------------------------

airflow_configuration_options = {
  "core.load_examples" = "False"
  "webserver.warn_deployment_exposure" = "False"
  #"core.dags_are_paused_at_creation" = "True"
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






