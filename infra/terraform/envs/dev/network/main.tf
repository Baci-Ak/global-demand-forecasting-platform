# ==============================================================================
# envs/dev/network/main.tf
# ==============================================================================
#
# Purpose
# - Deploy the dev network foundation (VPC + subnets) used by downstream services.
#
# Notes
# - Downstream stacks (RDS, MWAA, Redshift) consume outputs from this stack.
# ==============================================================================

module "network" {
  source = "../../../modules/network"

  project_name = var.project_name
  environment  = var.environment

  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  single_nat_gateway = var.single_nat_gateway
}



module "vpc_endpoints" {
  source = "../../../modules/vpc_endpoints"
  project_name = var.project_name
  environment = var.environment
  aws_region = var.aws_region
  vpc_id = module.network.vpc_id
  private_subnet_ids = module.network.private_subnet_ids
  private_route_table_ids = module.network.private_route_table_ids




  # Attach the shared workloads SG so MWAA can reach VPC Interface Endpoints.
  # The endpoints module grants inbound to this SG (not to the MWAA SG directly)
  # to avoid cross-stack coupling and keep endpoint access stable.

  consumer_security_groups = {
  workloads = module.network.workloads_security_group_id
}


  enable_s3_gateway_endpoint = true

  # ────────────────────────────────────────────────────────────────────────────────
  # Existing + ADD these three for full MWAA private networking
  # ────────────────────────────────────────────────────────────────────────────────
  interface_endpoints = [
    "logs",
    "sqs",
    "monitoring",
    "kms",
    "airflow.api",
    "airflow.env",
    "airflow.ops"
  ]

  enable_private_dns = true
}

