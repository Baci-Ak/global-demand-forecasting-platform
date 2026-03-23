# ==============================================================================
# modules/network/workloads_security_group_rules.tf
# ==============================================================================
#
# Purpose
# - Explicit outbound rules for the shared workloads security group.
# - Required so private workloads (ECS tasks, MWAA-attached workloads, etc.)
#   can reach VPC endpoints, AWS APIs, and other internal services.
# ==============================================================================

resource "aws_security_group_rule" "workloads_egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.workloads.id

  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]

  description = "Allow outbound traffic from shared internal workloads."
}