# ==============================================================================
# envs/dev/ssm-jumphost/terraform.tfvars
# ==============================================================================
#
# Purpose
# - Environment inputs for the dev SSM jump host stack.
# - Values here should be safe to commit (no secrets).
# ==============================================================================

project_name = "gdf"
environment  = "dev"
aws_region   = "us-east-1"
