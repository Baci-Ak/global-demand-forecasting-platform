# ==============================================================================
# modules/rds-postgres/networking.tf
# ==============================================================================
#
# Purpose
# - Create networking primitives required for RDS Postgres:
#   - DB subnet group (private subnets only)
#   - Security group for database access control
#
# Notes
# - The subnet group ensures the DB is placed in private subnets.
# - The security group is created without any ingress rules by default.
#   Ingress is added explicitly by the caller (least privilege).
# ==============================================================================

resource "aws_db_subnet_group" "this" {
  name       = "${var.project_name}-${var.environment}-db-subnets"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${var.project_name}-${var.environment}-db-subnets"
  }
}

resource "aws_security_group" "db" {
  name        = "${var.project_name}-${var.environment}-postgres-sg"
  description = "Security group for Postgres (ingress defined explicitly by caller)."
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.project_name}-${var.environment}-postgres-sg"
  }
}




# ------------------------------------------------------------------------------
# Optional ingress: allow Postgres access from a trusted security group.
# ------------------------------------------------------------------------------

resource "aws_security_group_rule" "postgres_from_trusted_sg" {
  count = var.trusted_source_sg_id == null ? 0 : 1

  type              = "ingress"
  security_group_id = aws_security_group.db.id

  from_port                = var.db_port
  to_port                  = var.db_port
  protocol                 = "tcp"
  source_security_group_id = var.trusted_source_sg_id

  description = "Allow Postgres access from the trusted source security group."
}
