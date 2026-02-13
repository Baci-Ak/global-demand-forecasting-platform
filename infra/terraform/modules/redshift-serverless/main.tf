# ==============================================================================
# modules/redshift-serverless/main.tf
# ==============================================================================
#
# Purpose
# - Provision Redshift Serverless (namespace + workgroup) inside a VPC.
# ==============================================================================

resource "aws_security_group" "redshift" {
  name        = "${var.project_name}-${var.environment}-redshift-sg"
  description = "Security group for Redshift Serverless workgroup."
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.project_name}-${var.environment}-redshift-sg"
  }
}

resource "aws_security_group_rule" "ingress_from_allowed_sgs" {
  for_each = toset(var.allowed_sg_ids)

  type                     = "ingress"
  security_group_id        = aws_security_group.redshift.id
  from_port                = var.port
  to_port                  = var.port
  protocol                 = "tcp"
  source_security_group_id = each.value
  description              = "Allow Redshift access from approved security groups."
}

resource "aws_security_group_rule" "egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.redshift.id
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow all egress."
}

resource "aws_redshiftserverless_namespace" "this" {
  namespace_name = "${var.project_name}-${var.environment}-redshift-ns"

  db_name             = var.database_name
  admin_username      = var.admin_username
  admin_user_password = var.admin_password

  tags = {
    Name = "${var.project_name}-${var.environment}-redshift-ns"
  }
}

resource "aws_redshiftserverless_workgroup" "this" {
  workgroup_name = "${var.project_name}-${var.environment}-redshift-wg"
  namespace_name = aws_redshiftserverless_namespace.this.namespace_name

  base_capacity = var.base_capacity

  subnet_ids         = var.subnet_ids
  security_group_ids = [aws_security_group.redshift.id]

  tags = {
    Name = "${var.project_name}-${var.environment}-redshift-wg"
  }
}
