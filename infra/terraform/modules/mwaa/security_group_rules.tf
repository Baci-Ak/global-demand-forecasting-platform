# ==============================================================================
# modules/mwaa/security_group_rules.tf
# ==============================================================================
#
# Purpose
# - Define ingress/egress rules for the MWAA security group.
#
# Notes
# - PRIVATE_ONLY: allow webserver access from trusted security groups (e.g., SSM jump host).
# - PUBLIC_ONLY: optionally allow webserver access from explicit CIDR blocks.
# ==============================================================================

# Allow webserver access from approved security groups (typical for PRIVATE_ONLY).
resource "aws_security_group_rule" "web_ingress_from_allowed_sgs" {
  for_each = toset(var.allowed_web_sg_ids)

  type                     = "ingress"
  security_group_id        = aws_security_group.mwaa.id
  from_port                = var.webserver_ingress_port
  to_port                  = var.webserver_ingress_port
  protocol                 = var.webserver_ingress_protocol
  source_security_group_id = each.value
  description              = "Allow MWAA webserver access from approved security groups."
}

# Optional: allow webserver access from CIDRs (typical for PUBLIC_ONLY with office IPs).
resource "aws_security_group_rule" "web_ingress_from_cidrs" {
  count = length(var.allowed_web_cidr_blocks) > 0 ? 1 : 0

  type              = "ingress"
  security_group_id = aws_security_group.mwaa.id
  from_port         = var.webserver_ingress_port
  to_port           = var.webserver_ingress_port
  protocol          = var.webserver_ingress_protocol
  cidr_blocks       = var.allowed_web_cidr_blocks
  description       = "Allow MWAA webserver access from approved CIDR blocks."
}

# Allow MWAA to reach AWS services and the internet via NAT (private subnets).
resource "aws_security_group_rule" "egress_all" {
  count             = var.enable_egress_all ? 1 : 0
  type              = "egress"
  security_group_id = aws_security_group.mwaa.id

  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]

  description = "Allow all outbound traffic."
}


