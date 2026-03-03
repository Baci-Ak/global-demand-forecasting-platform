# ==============================================================================
# terraform.tfvars
# ==============================================================================
# Non-secret environment inputs (safe to commit).
# IMPORTANT: Do NOT put passwords/keys here. Use AWS Secrets Manager / SSM.
# ==============================================================================

project_name = "gdf"
environment  = "dev"
aws_region   = "us-east-1"
