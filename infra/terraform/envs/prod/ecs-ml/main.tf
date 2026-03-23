# ==============================================================================
# envs/prod/ecs-ml/main.tf
# ==============================================================================
#
# Purpose
# - Provision the production ECS runtime for ML workloads.
# - Wire the prod environment inputs into the reusable ecs-ml-runtime module.
# - Keep all environment-specific values in terraform.tfvars, not hardcoded here.
# ==============================================================================

data "aws_secretsmanager_secret" "warehouse_dsn" {
  name = "${var.project_name}/${var.environment}/warehouse_dsn"
}

data "aws_ssm_parameter" "mlflow_tracking_uri" {
  count = var.create_task_definition ? 1 : 0
  name  = "/gdf/${var.environment}/mlflow/tracking_uri"
}

data "terraform_remote_state" "s3" {
  backend = "s3"
  config = merge(
    { key = "envs/prod/s3/terraform.tfstate", use_lockfile = true },
    yamldecode(file("${path.module}/remote_state.hcl"))
  )
}

data "terraform_remote_state" "redshift" {
  backend = "s3"
  config = merge(
    { key = "envs/prod/redshift/terraform.tfstate", use_lockfile = true },
    yamldecode(file("${path.module}/remote_state.hcl"))
  )
}

module "ecs_ml_runtime" {
  source = "../../../modules/ecs-ml-runtime"

  # ---------------------------------------------------------------------------
  # Global environment identity
  # ---------------------------------------------------------------------------
  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  # ---------------------------------------------------------------------------
  # ECS ML runtime naming
  # ---------------------------------------------------------------------------
  cluster_name        = var.cluster_name
  execution_role_name = var.execution_role_name
  log_group_name      = var.log_group_name
  log_stream_prefix   = var.log_stream_prefix
  task_family         = var.task_family
  container_name      = var.container_name
  create_task_definition = var.create_task_definition



  # ---------------------------------------------------------------------------
  # Runtime image
  # ---------------------------------------------------------------------------
  ml_runtime_image = var.ml_runtime_image


  warehouse_dsn_secret_arn = data.aws_secretsmanager_secret.warehouse_dsn.arn
  mlflow_tracking_uri      = var.create_task_definition ? data.aws_ssm_parameter.mlflow_tracking_uri[0].value : null
  mlflow_artifact_bucket_name = data.terraform_remote_state.s3.outputs.mlflow_artifacts_bucket_name

  bronze_bucket_name = data.terraform_remote_state.s3.outputs.bronze_bucket_name

  training_extracts_bucket_name = data.terraform_remote_state.s3.outputs.training_extracts_bucket_name

  redshift_copy_role_arn = data.terraform_remote_state.redshift.outputs.redshift_copy_role_arn

  # ---------------------------------------------------------------------------
  # Runtime sizing
  # ---------------------------------------------------------------------------
  task_cpu    = var.task_cpu
  task_memory = var.task_memory

  # ---------------------------------------------------------------------------
  # Observability
  # ---------------------------------------------------------------------------
  log_retention_in_days      = var.log_retention_in_days
  container_insights_enabled = var.container_insights_enabled

  # ---------------------------------------------------------------------------
  # Tags
  # ---------------------------------------------------------------------------
  tags = var.tags
}