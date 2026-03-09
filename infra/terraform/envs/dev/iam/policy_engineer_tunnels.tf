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
#   - Specific jumphost instance id from remote state, when it exists
# ==============================================================================

data "terraform_remote_state" "ssm_jumphost" {
  backend = "s3"

  config = {
    bucket       = "gdf-dev-tfstate-f6df28"
    key          = "envs/dev/ssm-jumphost/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}

locals {
  dev_jumphost_instance_id = try(
    data.terraform_remote_state.ssm_jumphost.outputs.jumphost_instance_id,
    null
  )

  tunnel_session_resources = local.dev_jumphost_instance_id == null ? [
    "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:document/AWS-StartPortForwardingSessionToRemoteHost"
  ] : [
    "arn:aws:ec2:${var.aws_region}:${data.aws_caller_identity.current.account_id}:instance/${local.dev_jumphost_instance_id}",
    "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:document/AWS-StartPortForwardingSessionToRemoteHost"
  ]
}

resource "aws_iam_policy" "engineer_tunnels" {
  name        = "${var.project_name}-${var.environment}-engineer-tunnels"
  description = "Minimal permissions for engineers to SSM tunnel to MWAA/RDS/Redshift using published SSM parameters."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # --- Read the non-secret connection coordinates ---
      {
        Sid    = "ReadGdfDevParameters"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/gdf/dev/*"
      },

      # --- Start SSM port-forward sessions ONLY to the jumphost when it exists ---
      {
        Sid    = "StartSessionToJumphostOnly"
        Effect = "Allow"
        Action = [
          "ssm:StartSession",
          "ssm:TerminateSession",
          "ssm:ResumeSession"
        ]
        Resource = local.tunnel_session_resources
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