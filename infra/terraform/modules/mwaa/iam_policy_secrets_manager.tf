# ==============================================================================
# modules/mwaa/iam_policy_secrets_manager.tf
# ==============================================================================
#
# Purpose
# - Allow MWAA tasks/startup script to read runtime secrets from AWS Secrets Manager.
#
# Design
# - Scope access to secrets under the project/environment prefix:
#     <project_name>/<environment>/*
#   This matches how the infra stacks create secrets:
#     gdf/dev/rds-postgres/master
#     gdf/dev/redshift/admin
# ==============================================================================

resource "aws_iam_role_policy" "mwaa_secretsmanager_read" {
  name = "${local.name_prefix}-secretsmanager-read"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SecretsManagerReadProjectEnvPrefix"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}/${var.environment}/*"
        ]
      }
    ]
  })
}
