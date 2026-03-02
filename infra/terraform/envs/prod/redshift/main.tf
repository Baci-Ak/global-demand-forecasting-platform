# ==============================================================================
# envs/dev/redshift/main.tf
# ==============================================================================
#
# Purpose
# - Dev Redshift Serverless stack.
# - Consumes dev network outputs (VPC + private subnets) from remote state.
# - Allows connectivity from the dev SSM jumphost security group.
# - Provisions Redshift Serverless via the reusable module.
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

module "redshift" {
  source = "../../../modules/redshift-serverless"

  project_name = var.project_name
  environment  = var.environment

  vpc_id        = data.terraform_remote_state.network.outputs.vpc_id
  subnet_ids    = data.terraform_remote_state.network.outputs.private_subnet_ids
  port          = var.port
  base_capacity = var.base_capacity

  database_name  = var.database_name
  admin_username = var.admin_username
  admin_password = random_password.redshift_admin.result

  # Allow private connectivity from:
  # - SSM jumphost (human access via SSM tunnels)
  # - Workloads SG (MWAA workers/scheduler and other private workloads)
  #
  # This keeps Redshift private (no public ingress) and scales cleanly as more
  # internal services are added behind the workloads SG.
  allowed_sg_ids = [
    data.terraform_remote_state.ssm_jumphost.outputs.jumphost_security_group_id,
    data.terraform_remote_state.network.outputs.workloads_security_group_id,
  ]



  # Redshift Serverless usage limits (cost cap)
  enable_usage_limits             = var.enable_usage_limits
  usage_limit_rpu_hours_per_day   = var.usage_limit_rpu_hours_per_day
  usage_limit_rpu_hours_per_week  = var.usage_limit_rpu_hours_per_week
  usage_limit_rpu_hours_per_month = var.usage_limit_rpu_hours_per_month
  usage_limit_breach_action       = var.usage_limit_breach_action


  enable_log_exports = var.enable_log_exports
}
