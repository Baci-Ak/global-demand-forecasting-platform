# ==============================================================================
# envs/dev/ssm-jumphost/main.tf
# ==============================================================================
#
# Purpose
# - Dev SSM jump host stack.
# - This stack will provision a minimal EC2 instance managed via AWS SSM.
#
# Notes
# - No SSH access.
# - No inbound ports from the internet.
# - Used only for secure port-forwarding into private resources (e.g. RDS).
# ==============================================================================

data "terraform_remote_state" "network" {
  backend = "s3"

  config = {
    bucket = "gdf-dev-tfstate-f6df28"
    key    = "envs/dev/network/terraform.tfstate"
    region = "us-east-1"
  }
}


data "terraform_remote_state" "iam" {
  backend = "s3"

  config = {
    bucket       = "gdf-dev-tfstate-f6df28"
    key          = "envs/dev/iam/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
    encrypt      = true
  }
}

# ------------------------------------------------------------------------------
# Compute inputs for the EC2 jump host
# ------------------------------------------------------------------------------

locals {
  # Place the jump host in the first public subnet.
  public_subnet_id = data.terraform_remote_state.network.outputs.public_subnet_ids[0]
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-kernel-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}
