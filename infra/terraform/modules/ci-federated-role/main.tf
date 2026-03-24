# ==============================================================================
# modules/ci-federated-role/main.tf
# ==============================================================================
#
# Purpose
# - Create a reusable federated IAM role for CI/CD systems such as GitHub Actions.
#
# Responsibilities
# - Create the IAM role with an OIDC trust policy.
# - Grant Terraform backend lock-table access.
# - Grant Terraform apply permissions for the MWAA stack resources.
#
# Notes
# - This module is intentionally focused on the MWAA deploy/apply use case.
# - Identity-provider details are parameterized so the module can be reused
#   across environments and potentially across CI systems later.
# ==============================================================================

# ------------------------------------------------------------------------------
# IAM role trust policy
# ------------------------------------------------------------------------------
resource "aws_iam_role" "this" {
  name = var.role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = var.oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = var.oidc_audience
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = var.oidc_subjects
          }
        }
      }
    ]
  })

  #tags = var.tags
  tags = {}
}

# ------------------------------------------------------------------------------
# Inline policy: Terraform backend lock-table access
# ------------------------------------------------------------------------------
resource "aws_iam_role_policy" "terraform_backend_lock" {
  name = "${var.role_name}-terraform-backend-lock"
  role = aws_iam_role.this.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TerraformStateLockTableAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:DescribeTable",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
          "dynamodb:UpdateItem"
        ]
        Resource = var.terraform_lock_table_arn
      }
    ]
  })
}

# ------------------------------------------------------------------------------
# Inline policy: MWAA Terraform apply permissions
# ------------------------------------------------------------------------------
resource "aws_iam_role_policy" "mwaa_apply" {
  name = "${var.role_name}-mwaa-apply"
  role = aws_iam_role.this.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "MwaaEnvironmentManage"
        Effect = "Allow"
        Action = [
          "airflow:GetEnvironment",
          "airflow:UpdateEnvironment",
          "airflow:PublishMetrics"
        ]
        Resource = var.mwaa_environment_arn
      },
      {
        Sid    = "IamReadWriteForMwaaExecutionRole"
        Effect = "Allow"
        Action = [
          "iam:GetRole",
          "iam:ListRolePolicies",
          "iam:GetRolePolicy",
          "iam:PutRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:ListAttachedRolePolicies",
          "iam:TagRole",
          "iam:UntagRole"
        ]
        Resource = var.mwaa_execution_role_arn
      },
      {
        Sid    = "ReadMlEcrRepositoryUrlFromSsm"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = var.ml_ecr_ssm_parameter_arn
      },
      {
        Sid    = "GetEcrAuthorizationToken"
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      {
        Sid    = "PushMlImagesToEcr"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:BatchGetImage",
          "ecr:PutImage"
        ]
        Resource = var.ml_ecr_repository_arn
      },
      {
        Sid    = "S3ListMwaaBucket"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = var.mwaa_bucket_arn
      },
      {
        Sid    = "S3ManageMwaaBucketObjects"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = var.mwaa_bucket_objects_arn
      },
      {
        Sid    = "CloudWatchLogsDescribeGlobal"
        Effect = "Allow"
        Action = [
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      },
      {
        Sid    = "CloudWatchLogsManageForMwaa"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:DeleteLogGroup",
          "logs:ListTagsForResource",
          "logs:TagResource",
          "logs:UntagResource",
          "logs:PutRetentionPolicy",
          "logs:DeleteRetentionPolicy"
        ]
        Resource = [
          "${var.cloudwatch_log_group_prefix}*",
          "${var.cloudwatch_log_group_prefix}*:*"
        ]
      },
      {
        Sid    = "Ec2SecurityGroupReadForMwaa"
        Effect = "Allow"
        Action = [
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeSecurityGroupRules",
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets",
          "ec2:DescribeRouteTables",
          "ec2:DescribeDhcpOptions",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeNetworkInterfacePermissions"
        ]
        Resource = "*"
      },
      {
        Sid    = "Ec2SecurityGroupRuleManageForMwaa"
        Effect = "Allow"
        Action = [
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:AuthorizeSecurityGroupEgress",
          "ec2:RevokeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupEgress",
          "ec2:CreateSecurityGroup",
          "ec2:DeleteSecurityGroup",
          "ec2:CreateTags",
          "ec2:DeleteTags"
        ]
        Resource = "*"
      }
    ]
  })
}