# ==============================================================================
# modules/mwaa/iam_policy_ssm_parameters.tf
# ==============================================================================
#
# Purpose
# - Allow MWAA to read non-secret runtime coordinates from SSM Parameter Store.
# - This is needed for DAGs that dynamically discover ECS / MLflow runtime values.
# ==============================================================================

resource "aws_iam_role_policy" "mwaa_ssm_parameter_read" {
  name = "${local.name_prefix}-ssm-parameter-read"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadProjectEnvParameters"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${var.project_name}/${var.environment}/*"
        ]
      }
    ]
  })
}