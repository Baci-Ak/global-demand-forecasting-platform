# ==============================================================================
# envs/prod/ecs-ml/terraform.tfvars
# ==============================================================================
#
# Purpose
# - Environment inputs for the production ECS ML runtime stack.
# - Keep all sizing, naming, logging, and image values explicit.
# ==============================================================================

# ------------------------------------------------------------------------------
# Global environment identity
# ------------------------------------------------------------------------------

project_name = "gdf"
environment  = "prod"
aws_region   = "us-east-1"

# ------------------------------------------------------------------------------
# ECS ML runtime naming
# ------------------------------------------------------------------------------

cluster_name        = "gdf-prod-ml-runtime"
execution_role_name = "gdf-prod-ecs-ml-execution"
log_group_name      = "/ecs/gdf-prod-ml-runtime"
log_stream_prefix   = "ml-runtime"
task_family         = "gdf-prod-ml-runtime"
container_name      = "ml-runtime"

# ------------------------------------------------------------------------------
# Runtime image
# ------------------------------------------------------------------------------

#create_task_definition = false

#set these two values when the runtime image is in was ECR repository
create_task_definition = true
ml_runtime_image       = "697980229152.dkr.ecr.us-east-1.amazonaws.com/gdf-prod-ml-runtime:latest"

# repository URI = 798329741238.dkr.ecr.us-east-1.amazonaws.com/gdf-prod-ml-runtime
# current tag = current tag



# ------------------------------------------------------------------------------
# ECS ML runtime memory sizing
# ------------------------------------------------------------------------------

task_cpu    = 4096
task_memory = 16384

# ------------------------------------------------------------------------------
# Observability
# ------------------------------------------------------------------------------

log_retention_in_days       = 30
container_insights_enabled  = true

# ------------------------------------------------------------------------------
# Tags
# ------------------------------------------------------------------------------

tags = {
  component = "ecs-ml-runtime"
}