# ==============================================================================
# envs/prod/mlflow/main.tf
# ==============================================================================
#
# Purpose
# - Provision the production MLflow runtime in AWS.
# - Run MLflow as a private ECS/Fargate service behind an internal ALB.
# - Use:
#   - RDS/Postgres backend store secret from Secrets Manager
#   - S3 artifact bucket from the prod S3 stack
#   - ECS cluster from the prod ecs-ml stack
# ==============================================================================

# ------------------------------------------------------------------------------
# Remote state: network
# ------------------------------------------------------------------------------

data "terraform_remote_state" "network" {
  backend = "s3"
  config = merge(
    { key = "envs/prod/network/terraform.tfstate", use_lockfile = true },
    yamldecode(file("${path.module}/remote_state.hcl"))
  )
}

data "terraform_remote_state" "ssm_jumphost" {
  backend = "s3"
  config = merge(
    { key = "envs/prod/ssm-jumphost/terraform.tfstate", use_lockfile = true },
    yamldecode(file("${path.module}/remote_state.hcl"))
  )
}

# ------------------------------------------------------------------------------
# Remote state: s3
# ------------------------------------------------------------------------------

data "terraform_remote_state" "s3" {
  backend = "s3"
  config = merge(
    { key = "envs/prod/s3/terraform.tfstate", use_lockfile = true },
    yamldecode(file("${path.module}/remote_state.hcl"))
  )
}

# ------------------------------------------------------------------------------
# Remote state: ecs-ml
# ------------------------------------------------------------------------------

data "terraform_remote_state" "ecs_ml" {
  backend = "s3"
  config = merge(
    { key = "envs/prod/ecs-ml/terraform.tfstate", use_lockfile = true },
    yamldecode(file("${path.module}/remote_state.hcl"))
  )
}


# ------------------------------------------------------------------------------
# Secrets Manager: MLflow backend store URI
# ------------------------------------------------------------------------------

data "aws_secretsmanager_secret" "mlflow_backend_store" {
  name = var.mlflow_backend_store_secret_id
}

# ------------------------------------------------------------------------------
# MLflow ECS service
# ------------------------------------------------------------------------------

module "mlflow_service" {
  source = "../../../modules/mlflow-ecs-service"

  # ---------------------------------------------------------------------------
  # Global identity
  # ---------------------------------------------------------------------------
  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  # ---------------------------------------------------------------------------
  # ECS cluster
  # ---------------------------------------------------------------------------
  ecs_cluster_arn = data.terraform_remote_state.ecs_ml.outputs.ecs_cluster_arn

  # ---------------------------------------------------------------------------
  # Networking
  # ---------------------------------------------------------------------------
  vpc_id             = data.terraform_remote_state.network.outputs.vpc_id
  private_subnet_ids = data.terraform_remote_state.network.outputs.private_subnet_ids

  allowed_ingress_security_group_ids = [
    data.terraform_remote_state.network.outputs.workloads_security_group_id,
    data.terraform_remote_state.ssm_jumphost.outputs.jumphost_security_group_id
  ]

  additional_task_security_group_ids = [
    data.terraform_remote_state.network.outputs.workloads_security_group_id
  ]

  # ---------------------------------------------------------------------------
  # Naming
  # ---------------------------------------------------------------------------
  service_name        = var.service_name
  task_family         = var.task_family
  execution_role_name = var.execution_role_name
  task_role_name      = var.task_role_name
  log_group_name      = var.log_group_name
  log_stream_prefix   = var.log_stream_prefix

  # ---------------------------------------------------------------------------
  # Container runtime
  # ---------------------------------------------------------------------------
  mlflow_image   = var.mlflow_image
  container_name = var.container_name
  container_port = var.container_port
  desired_count  = var.desired_count
  task_cpu       = var.task_cpu
  task_memory    = var.task_memory

  # ---------------------------------------------------------------------------
  # MLflow configuration
  # ---------------------------------------------------------------------------
  mlflow_backend_store_secret_arn = data.aws_secretsmanager_secret.mlflow_backend_store.arn
  mlflow_artifact_bucket_name     = data.terraform_remote_state.s3.outputs.mlflow_artifacts_bucket_name

  # ---------------------------------------------------------------------------
  # Logging / observability
  # ---------------------------------------------------------------------------
  log_retention_in_days = var.log_retention_in_days
  health_check_path     = var.health_check_path

  # ---------------------------------------------------------------------------
  # Tags
  # ---------------------------------------------------------------------------
  tags = var.tags
}