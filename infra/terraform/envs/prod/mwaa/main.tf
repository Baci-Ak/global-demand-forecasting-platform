# ==============================================================================
# envs/dev/mwaa/main.tf
# ==============================================================================
#
# Purpose
# - Dev MWAA stack.
# - Runs MWAA in private subnets from the dev network stack.
# - Webserver is PRIVATE_ONLY and reachable from the dev SSM jumphost SG.
# ==============================================================================

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

data "terraform_remote_state" "s3" {
  backend = "s3"
  config = merge(
    { key = "envs/prod/s3/terraform.tfstate", use_lockfile = true },
    yamldecode(file("${path.module}/remote_state.hcl"))
  )
}


data "terraform_remote_state" "ecs_ml" {
  backend = "s3"
  config = merge(
    { key = "envs/prod/ecs-ml/terraform.tfstate", use_lockfile = true },
    yamldecode(file("${path.module}/remote_state.hcl"))
  )
}




module "mwaa" {
  source = "../../../modules/mwaa"

  project_name = var.project_name
  environment  = var.environment

  airflow_version   = var.airflow_version
  environment_class = var.environment_class
  min_workers       = var.min_workers
  max_workers       = var.max_workers


  cloudwatch_log_retention_days = var.cloudwatch_log_retention_days


  webserver_access_mode = var.webserver_access_mode

  vpc_id             = data.terraform_remote_state.network.outputs.vpc_id
  private_subnet_ids = data.terraform_remote_state.network.outputs.private_subnet_ids
  additional_security_group_ids = [
    data.terraform_remote_state.network.outputs.workloads_security_group_id
  ]


  allowed_web_sg_ids = [
    data.terraform_remote_state.ssm_jumphost.outputs.jumphost_security_group_id
  ]

  allowed_web_cidr_blocks    = var.allowed_web_cidr_blocks
  webserver_ingress_port     = var.webserver_ingress_port
  webserver_ingress_protocol = var.webserver_ingress_protocol
  enable_egress_all          = var.enable_egress_all

  dag_s3_bucket = data.terraform_remote_state.s3.outputs.airflow_bucket_name
  dag_s3_path   = var.dag_s3_path

  requirements_s3_path   = var.requirements_s3_path
  plugins_s3_path        = var.plugins_s3_path
  startup_script_s3_path = var.startup_script_s3_path


  requirements_s3_object_version   = var.requirements_s3_path == null ? null : data.aws_s3_object.requirements[0].version_id
  plugins_s3_object_version        = var.plugins_s3_path == null ? null : data.aws_s3_object.plugins[0].version_id
  startup_script_s3_object_version = var.startup_script_s3_path == null ? null : data.aws_s3_object.startup[0].version_id

  airflow_configuration_options = var.airflow_configuration_options

  data_bucket_names = [
  data.terraform_remote_state.s3.outputs.bronze_bucket_name,
  data.terraform_remote_state.s3.outputs.forecast_application_bucket_name
]
 



  logging_configuration = var.logging_configuration

  ecs_ml_cluster_arn         = data.terraform_remote_state.ecs_ml.outputs.ecs_cluster_arn
  ecs_ml_task_definition_arn = try(data.terraform_remote_state.ecs_ml.outputs.task_definition_arn, null)
  ecs_ml_task_role_arn       = data.terraform_remote_state.ecs_ml.outputs.task_role_arn
  ecs_ml_execution_role_arn  = data.terraform_remote_state.ecs_ml.outputs.task_execution_role_arn
}
