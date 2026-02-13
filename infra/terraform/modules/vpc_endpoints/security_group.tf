# ==============================================================================
# modules/vpc_endpoints/security_group.tf
# ==============================================================================
#
# Purpose
# - Security group for interface VPC endpoints.
#
# Notes
# - Interface endpoints are ENIs in your subnets. They must allow HTTPS (443)
#   from the workload SGs (e.g., MWAA).
# ==============================================================================



resource "aws_security_group" "vpce" {
  name        = "${local.name_prefix}-vpce-sg"
  description = "Security group for VPC interface endpoints."
  vpc_id      = var.vpc_id

  tags = merge(
    { Name = "${local.name_prefix}-vpce-sg" },
    var.tags
  )
}

resource "aws_security_group_rule" "vpce_ingress_https_from_consumers" {
  for_each = var.consumer_security_groups

  type                     = "ingress"
  security_group_id        = aws_security_group.vpce.id
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = each.value
  description              = "Allow HTTPS from approved consumer security groups."
}

resource "aws_security_group_rule" "vpce_egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.vpce.id
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow outbound traffic (endpoint ENIs)."
}
