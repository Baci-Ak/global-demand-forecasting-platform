# ==============================================================================
# envs/dev/network/terraform.tfvars
# ==============================================================================
#
# Purpose
# - Environment inputs for the dev network stack.
# - Values here should be safe to commit (no secrets).
# ==============================================================================



project_name = "gdf"
environment  = "prod"
aws_region   = "us-east-1"


# ------------------------------------------------------------------------------
# VPC design 
# ------------------------------------------------------------------------------

vpc_cidr = "10.20.0.0/16"

availability_zones = [
  "us-east-1a",
  "us-east-1b"
]

# Cost-conscious dev default:
# - 1 NAT Gateway shared by private subnets
single_nat_gateway = false
