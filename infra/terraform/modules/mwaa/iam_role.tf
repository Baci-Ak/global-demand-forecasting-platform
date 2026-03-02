# ==============================================================================
# modules/mwaa/iam_role.tf
# ==============================================================================
#
# Purpose
# - Define the MWAA execution role assumed by the MWAA service.
#
# Notes
# - Policies are attached in separate files to keep concerns isolated.
# ==============================================================================

resource "aws_iam_role" "mwaa_execution" {
  name = "${local.name_prefix}-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "airflow.amazonaws.com" }
        Action    = "sts:AssumeRole"
      },
      {
        Effect    = "Allow"
        Principal = { Service = "airflow-env.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(
    { Name = "${local.name_prefix}-execution-role" },
    var.tags
  )
}
