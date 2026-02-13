# ==============================================================================
# envs/dev/ssm-jumphost/instance.tf
# ==============================================================================
#
# Purpose
# - Provision a minimal EC2 instance used as an SSM-managed jump host.
#
# Notes
# - No SSH keypair is attached (SSM-only).
# - No inbound security group rules are defined (no open ports).
# - Instance is placed in a public subnet so it can reach SSM without needing
#   VPC endpoints (simplifies dev).
# ==============================================================================

resource "aws_instance" "jumphost" {
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = "t3.micro"

  subnet_id              = local.public_subnet_id
  vpc_security_group_ids = [aws_security_group.jumphost.id]

  iam_instance_profile = aws_iam_instance_profile.ssm_jumphost.name

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-ssm-jumphost"
  }
}
