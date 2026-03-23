# ==============================================================================
# envs/prod/monitoring/ssm_params.tf
# ==============================================================================
#
# Purpose
# - Publish NON-SECRET infrastructure coordinates to SSM Parameter Store.
# - Allows engineers and operational scripts to discover runtime services
#   without accessing Terraform state or the repository.
#
# Stored values
# - jumphost instance id
# - MWAA webserver host
# - RDS endpoint host + port
# - Redshift endpoint host + port
# - ML runtime ECS cluster name
#
# Design principles
# - Only store NON-SECRET values here.
# - Secrets remain in AWS Secrets Manager.
# - Parameter names follow: /gdf/<env>/<service>/<key>
# ==============================================================================

# ------------------------------------------------------------------------------
# Base path
# ------------------------------------------------------------------------------

locals {
  ssm_base = "/gdf/${var.environment}"

  mwaa_webserver_host = trimsuffix(
    trimprefix(data.terraform_remote_state.mwaa.outputs.mwaa_webserver_url, "https://"),
    "/"
  )
}

# ------------------------------------------------------------------------------
# Dev access helpers
# ------------------------------------------------------------------------------

resource "aws_ssm_parameter" "jumphost_instance_id" {
  name      = "${local.ssm_base}/ssm/jumphost_instance_id"
  type      = "String"
  value     = data.terraform_remote_state.ssm_jumphost.outputs.jumphost_instance_id
  overwrite = true
}

# ------------------------------------------------------------------------------
# MWAA
# ------------------------------------------------------------------------------

resource "aws_ssm_parameter" "mwaa_webserver_host" {
  name      = "${local.ssm_base}/mwaa/webserver_host"
  type      = "String"
  value     = local.mwaa_webserver_host
  overwrite = true
}

# ------------------------------------------------------------------------------
# RDS (audit DB)
# ------------------------------------------------------------------------------

resource "aws_ssm_parameter" "rds_endpoint_host" {
  name      = "${local.ssm_base}/rds/endpoint_host"
  type      = "String"
  value     = data.terraform_remote_state.rds.outputs.endpoint
  overwrite = true
}

resource "aws_ssm_parameter" "rds_port" {
  name      = "${local.ssm_base}/rds/port"
  type      = "String"
  value     = tostring(data.terraform_remote_state.rds.outputs.port)
  overwrite = true
}

# ------------------------------------------------------------------------------
# Redshift (warehouse)
# ------------------------------------------------------------------------------

resource "aws_ssm_parameter" "redshift_endpoint_host" {
  name      = "${local.ssm_base}/redshift/endpoint_host"
  type      = "String"
  value     = data.terraform_remote_state.redshift.outputs.endpoint
  overwrite = true
}

resource "aws_ssm_parameter" "redshift_port" {
  name      = "${local.ssm_base}/redshift/port"
  type      = "String"
  value     = tostring(data.terraform_remote_state.redshift.outputs.port)
  overwrite = true
}

# ------------------------------------------------------------------------------
# ML runtime (ECS)
# ------------------------------------------------------------------------------

resource "aws_ssm_parameter" "ml_runtime_cluster_name" {
  name      = "${local.ssm_base}/ecs/ml_runtime_cluster_name"
  type      = "String"
  value     = data.terraform_remote_state.ecs_ml.outputs.ecs_cluster_name
  overwrite = true
}

# ------------------------------------------------------------------------------
# ML runtime image repository
# ------------------------------------------------------------------------------

resource "aws_ssm_parameter" "ml_ecr_repository_url" {
  name      = "${local.ssm_base}/ecr/ml_repository_url"
  type      = "String"
  value     = data.terraform_remote_state.ecr_ml.outputs.ml_ecr_repository_url
  overwrite = true
}



resource "aws_ssm_parameter" "ml_runtime_task_role_arn" {
  name      = "${local.ssm_base}/ecs/ml_runtime_task_role_arn"
  type      = "String"
  value     = data.terraform_remote_state.ecs_ml.outputs.task_role_arn
  overwrite = true
}



resource "aws_ssm_parameter" "mlflow_tracking_uri" {
  name      = "${local.ssm_base}/mlflow/tracking_uri"
  type      = "String"
  value     = data.terraform_remote_state.mlflow.outputs.tracking_uri
  overwrite = true
}

resource "aws_ssm_parameter" "mlflow_host" {
  name      = "${local.ssm_base}/mlflow/host"
  type      = "String"
  value     = data.terraform_remote_state.mlflow.outputs.alb_dns_name
  overwrite = true
}



resource "aws_ssm_parameter" "ecs_ml_private_subnet_ids" {
  name      = "${local.ssm_base}/ecs/ml_runtime_private_subnet_ids"
  type      = "StringList"
  value     = join(",", data.terraform_remote_state.network.outputs.private_subnet_ids)
  overwrite = true
}

resource "aws_ssm_parameter" "ecs_ml_security_group_id" {
  name      = "${local.ssm_base}/ecs/ml_runtime_security_group_id"
  type      = "String"
  value     = data.terraform_remote_state.network.outputs.workloads_security_group_id
  overwrite = true
}

resource "aws_ssm_parameter" "ecs_ml_task_definition_family" {
  count     = try(data.terraform_remote_state.ecs_ml.outputs.task_definition_family, null) == null ? 0 : 1
  name      = "${local.ssm_base}/ecs/ml_runtime_task_definition_family"
  type      = "String"
  value     = data.terraform_remote_state.ecs_ml.outputs.task_definition_family
  overwrite = true
}