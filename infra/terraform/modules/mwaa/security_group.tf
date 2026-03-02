# ==============================================================================
# modules/mwaa/security_group.tf
# ==============================================================================
#
# Purpose
# - Create the security group attached to the MWAA environment ENIs.
#
# Notes
# - Ingress/egress rules are defined in security_group_rules.tf to keep the SG
#   resource easy to locate and review.
# ==============================================================================

resource "aws_security_group" "mwaa" {
  name        = "${local.name_prefix}-sg"
  description = "Security group for MWAA environment."
  vpc_id      = var.vpc_id

  tags = merge(
    { Name = "${local.name_prefix}-sg" },
    var.tags
  )
}

# Allow internal MWAA component communication (self-referencing).
resource "aws_security_group_rule" "internal_self" {
  type              = "ingress"
  security_group_id = aws_security_group.mwaa.id

  from_port = 0
  to_port   = 0
  protocol  = "-1"

  source_security_group_id = aws_security_group.mwaa.id
  description              = "Allow internal MWAA component communication (self-referencing)."
}

