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
  iam_roles           = [aws_iam_role.redshift_copy_role.arn]

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


  # User activity logging (Serverless-supported)
  # Note: Serverless does NOT support classic "log_exports" lists like provisioned clusters.
  config_parameter {
    parameter_key   = "enable_user_activity_logging"
    parameter_value = var.enable_log_exports ? "true" : "false"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-redshift-wg"
  }
}





# ------------------------------------------------------------------------------
# IAM role for Redshift COPY from S3
# ------------------------------------------------------------------------------

resource "aws_iam_role" "redshift_copy_role" {
  name = "${var.project_name}-${var.environment}-redshift-copy-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "redshift.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "redshift_copy_s3_policy" {
  name = "${var.project_name}-${var.environment}-redshift-copy-s3"
  role = aws_iam_role.redshift_copy_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = "*"
      }
    ]
  })
}







# ------------------------------------------------------------------------------
# Usage limits (cost guardrails)
# - These limits protect you from accidental runaway usage.
# - Use 'log' first in dev to observe; use 'deactivate' in prod for hard-stop.
# ------------------------------------------------------------------------------

resource "aws_redshiftserverless_usage_limit" "daily_rpu_hours" {
  count = var.enable_usage_limits && var.usage_limit_rpu_hours_per_day != null ? 1 : 0

  resource_arn  = aws_redshiftserverless_workgroup.this.arn
  usage_type    = "serverless-compute"
  period        = "daily"
  amount        = var.usage_limit_rpu_hours_per_day
  breach_action = var.usage_limit_breach_action
}

resource "aws_redshiftserverless_usage_limit" "weekly_rpu_hours" {
  count = var.enable_usage_limits && var.usage_limit_rpu_hours_per_week != null ? 1 : 0

  resource_arn  = aws_redshiftserverless_workgroup.this.arn
  usage_type    = "serverless-compute"
  period        = "weekly"
  amount        = var.usage_limit_rpu_hours_per_week
  breach_action = var.usage_limit_breach_action
}

resource "aws_redshiftserverless_usage_limit" "monthly_rpu_hours" {
  count = var.enable_usage_limits && var.usage_limit_rpu_hours_per_month != null ? 1 : 0

  resource_arn  = aws_redshiftserverless_workgroup.this.arn
  usage_type    = "serverless-compute"
  period        = "monthly"
  amount        = var.usage_limit_rpu_hours_per_month
  breach_action = var.usage_limit_breach_action
}