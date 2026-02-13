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

  config = {
    bucket       = "gdf-dev-tfstate-f6df28"
    key          = "envs/dev/network/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}

data "terraform_remote_state" "ssm_jumphost" {
  backend = "s3"

  config = {
    bucket       = "gdf-dev-tfstate-f6df28"
    key          = "envs/dev/ssm-jumphost/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
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

  dag_s3_bucket = var.dag_s3_bucket
  dag_s3_path   = var.dag_s3_path

  requirements_s3_path   = var.requirements_s3_path
  plugins_s3_path        = var.plugins_s3_path
  startup_script_s3_path = var.startup_script_s3_path

  airflow_configuration_options = var.airflow_configuration_options
  logging_configuration         = var.logging_configuration
}
