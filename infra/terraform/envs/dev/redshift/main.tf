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

  allowed_sg_ids = [
    data.terraform_remote_state.ssm_jumphost.outputs.jumphost_security_group_id
  ]
}
