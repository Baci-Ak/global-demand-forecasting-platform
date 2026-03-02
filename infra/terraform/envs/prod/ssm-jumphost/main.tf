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
  config = merge(
  { key = "envs/prod/network/terraform.tfstate" },
  yamldecode(file("${path.module}/remote_state.hcl"))
)
}


data "terraform_remote_state" "iam" {
  backend = "s3"
  config = merge(
  { key = "envs/prod/iam/terraform.tfstate", use_lockfile = true },
  yamldecode(file("${path.module}/remote_state.hcl"))
)
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
