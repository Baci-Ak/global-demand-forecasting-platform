# ==============================================================================
# envs/prod/mlflow/terraform.tfvars
# ==============================================================================
#
# Purpose
# - Environment inputs for the production MLflow ECS service stack.
# - Keep all sizing, naming, image, and secret values explicit.
# ==============================================================================

# ------------------------------------------------------------------------------
# Global environment identity
# ------------------------------------------------------------------------------

project_name = "gdf"
environment  = "prod"
aws_region   = "us-east-1"

# ------------------------------------------------------------------------------
# Naming
# ------------------------------------------------------------------------------

service_name        = "mlflow"
task_family         = "gdf-prod-mlflow"
execution_role_name = "gdf-prod-mlflow-execution"
task_role_name      = "gdf-prod-mlflow-task"
log_group_name      = "/ecs/gdf-prod-mlflow"
log_stream_prefix   = "mlflow"

# ------------------------------------------------------------------------------
# Container runtime
# ------------------------------------------------------------------------------
# Set this to the production MLflow image you will push to ECR.
# Example:
# 798329741238.dkr.ecr.us-east-1.amazonaws.com/gdf-prod-mlflow:latest
# ------------------------------------------------------------------------------

# always change this settings if the ECR image URI change
mlflow_image   = "697980229152.dkr.ecr.us-east-1.amazonaws.com/gdf-prod-ml-runtime:mlflow-2.14.3"
container_name = "mlflow"
container_port = 5000
desired_count  = 1
task_cpu       = 1024
task_memory    = 2048

# ------------------------------------------------------------------------------
# MLflow configuration
# ------------------------------------------------------------------------------
# This should point to the secret that stores the Postgres backend store URI
# for MLflow metadata.
# ------------------------------------------------------------------------------

mlflow_backend_store_secret_id = "gdf/prod/mlflow_postgres_dsn"

# ------------------------------------------------------------------------------
# Logging / observability
# ------------------------------------------------------------------------------

log_retention_in_days = 30
health_check_path     = "/"

# ------------------------------------------------------------------------------
# Tags
# ------------------------------------------------------------------------------

tags = {
  component = "mlflow"
}