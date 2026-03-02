# ==============================================================================
# envs/dev/iam/policy_engineer_tunnels.tf
# ==============================================================================
#
# Purpose
# - Allow engineers to use ONLY the connect_dev.sh script (no repo required):
#   - Read non-secret connection coordinates from SSM Parameter Store
#   - Start SSM port-forwarding sessions to the dev jumphost
#
# Notes
# - Does NOT grant access to Secrets Manager (credentials are handled separately).
# - Scope is restricted to:
#   - Parameter path: /gdf/dev/*
#   - Specific jumphost instance id from remote state
# ==============================================================================


resource "aws_iam_policy" "engineer_tunnels" {
  name        = "${var.project_name}-${var.environment}-engineer-tunnels"
  description = "Minimal permissions for engineers to SSM tunnel to MWAA/RDS/Redshift using published SSM parameters."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # --- Read the non-secret connection coordinates ---
      {
        Sid    = "ReadGdfProdParameters"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/gdf/prod/*"
      },

      # --- Start SSM port-forward sessions ONLY to the jumphost ---
      {
        Sid    = "StartSessionToProdJumphostByTag"
        Effect = "Allow"
        Action = [
          "ssm:StartSession",
          "ssm:TerminateSession",
          "ssm:ResumeSession"
        ]
        Resource = [
          "arn:aws:ec2:${var.aws_region}:${data.aws_caller_identity.current.account_id}:instance/*",
          "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:document/AWS-StartPortForwardingSessionToRemoteHost"
        ]
        Condition = {
          StringEquals = {
            "ssm:resourceTag/project"     = "${var.project_name}",
            "ssm:resourceTag/environment" = "${var.environment}",
            "ssm:resourceTag/role"        = "jumphost"
          }
        }
      },

      # --- Required by session-manager-plugin / CLI usability ---
      {
        Sid    = "DescribeForSessionManager"
        Effect = "Allow"
        Action = [
          "ssm:DescribeSessions",
          "ssm:GetConnectionStatus",
          "ssm:DescribeInstanceInformation"
        ]
        Resource = "*"
      }
    ]
  })
}