# ==============================================================================
# envs/dev/rds-postgres/main.tf
# ==============================================================================
#
# Purpose
# - Dev RDS Postgres stack.
# - Consumes dev network outputs (VPC + private subnets) from remote state.
# - Provisions a Postgres instance using credentials stored in Secrets Manager.
#
# Notes
# - Secrets are generated and stored in Secrets Manager by this stack.
# - The DB module consumes the same generated values directly to avoid
#   eventual-consistency issues when reading secret versions during apply.
# ==============================================================================

data "terraform_remote_state" "network" {
  backend = "s3"

  config = {
    bucket = "gdf-dev-tfstate-f6df28"
    key    = "envs/dev/network/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "ssm_jumphost" {
  backend = "s3"

  config = {
    bucket = "gdf-dev-tfstate-f6df28"
    key    = "envs/dev/ssm-jumphost/terraform.tfstate"
    region = "us-east-1"
  }
}



data "terraform_remote_state" "iam" {
  backend = "s3"

  config = {
    bucket       = "gdf-dev-tfstate-f6df28"
    key          = "envs/dev/iam/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}


module "rds_postgres" {
  source = "../../../modules/rds-postgres"

  project_name = var.project_name
  environment  = var.environment

  vpc_id             = data.terraform_remote_state.network.outputs.vpc_id
  private_subnet_ids = data.terraform_remote_state.network.outputs.private_subnet_ids

  db_name         = var.db_name
  master_username = var.db_username
  master_password = random_password.db_master.result
  db_port         = var.db_port


  engine_version        = var.engine_version
  instance_class        = var.instance_class
  allocated_storage_gb  = var.allocated_storage_gb
  backup_retention_days = var.backup_retention_days
  publicly_accessible   = var.publicly_accessible
  deletion_protection   = var.deletion_protection
  skip_final_snapshot   = var.skip_final_snapshot
  trusted_source_sg_id  = data.terraform_remote_state.ssm_jumphost.outputs.jumphost_security_group_id


  # Allow MWAA (via the shared workloads SG) to reach Postgres privately.
  additional_trusted_source_sg_ids = [
    data.terraform_remote_state.network.outputs.workloads_security_group_id
  ]


}
