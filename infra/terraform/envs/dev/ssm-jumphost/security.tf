# ==============================================================================
# envs/dev/ssm-jumphost/security.tf
# ==============================================================================
#
# Purpose
# - Security group for the SSM-managed jump host.
#
# Notes
# - No inbound rules: the instance is managed via AWS Systems Manager (SSM),
#   not via SSH.
# - Egress is allowed so the instance can reach AWS APIs (SSM) and download
#   updates if needed.
# ==============================================================================

resource "aws_security_group" "jumphost" {
  name        = "${var.project_name}-${var.environment}-ssm-jumphost-sg"
  description = "Security group for SSM jump host (no inbound; SSM-managed)."
  vpc_id      = data.terraform_remote_state.network.outputs.vpc_id

  tags = {
    Name = "${var.project_name}-${var.environment}-ssm-jumphost-sg"
  }
}

resource "aws_security_group_rule" "egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.jumphost.id

  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]

  description = "Allow all outbound traffic."
}
