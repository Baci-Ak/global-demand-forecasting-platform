# ==============================================================================
# modules/network/workloads_security_group.tf
# ==============================================================================
#
# Purpose
# - Create a shared security group for "workloads" that run inside the VPC.
#
# Why this exists
# - Keeps the foundation stack independent of downstream stacks.
# - Provides a stable SG that downstream services can attach to.
# - Enables shared controls (e.g., VPC endpoints ingress) without cross-stack
#   remote-state dependencies.
# ==============================================================================

resource "aws_security_group" "workloads" {
  name        = "${var.project_name}-${var.environment}-workloads-sg"
  description = "Shared security group for internal workloads in the VPC."
  vpc_id      = aws_vpc.this.id

  tags = {
    Name = "${var.project_name}-${var.environment}-workloads-sg"
  }
}


