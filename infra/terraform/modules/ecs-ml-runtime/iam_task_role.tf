# ==============================================================================
# modules/ecs-ml-runtime/iam_task_role.tf
# ==============================================================================
#
# Purpose
# - IAM role assumed by the ML runtime container itself.
# - This is separate from the ECS execution role.
#
# Execution role
#   -> pulls images from ECR
#   -> writes logs to CloudWatch
#
# Task role
#   -> what the ML code is allowed to access:
#        - S3 (training data / artifacts)
#        - Secrets Manager (DB credentials)
#        - SSM Parameter Store (non-secret runtime config)
#        - MLflow artifact bucket
#
# Design principles
# - Least privilege
# - Explicit permissions
# - No wildcard service access
# ==============================================================================

# ------------------------------------------------------------------------------
# Task role
# ------------------------------------------------------------------------------

resource "aws_iam_role" "task_role" {
  name = "${var.project_name}-${var.environment}-ecs-ml-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(
    {
      Name = "${var.project_name}-${var.environment}-ecs-ml-task"
    },
    var.tags
  )
}

# ------------------------------------------------------------------------------
# Policy: read runtime configuration
# ------------------------------------------------------------------------------

resource "aws_iam_policy" "runtime_config" {
  name = "${var.project_name}-${var.environment}-ecs-ml-runtime-config"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = "arn:aws:ssm:*:*:parameter/gdf/${var.environment}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "runtime_config" {
  role       = aws_iam_role.task_role.name
  policy_arn = aws_iam_policy.runtime_config.arn
}

# ------------------------------------------------------------------------------
# Policy: read secrets
# ------------------------------------------------------------------------------

resource "aws_iam_policy" "secrets_access" {
  name = "${var.project_name}-${var.environment}-ecs-ml-secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:*:*:secret:gdf/${var.environment}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "secrets_access" {
  role       = aws_iam_role.task_role.name
  policy_arn = aws_iam_policy.secrets_access.arn
}

# ------------------------------------------------------------------------------
# Policy: S3 access for data + artifacts
# ------------------------------------------------------------------------------

resource "aws_iam_policy" "s3_data_access" {
  name = "${var.project_name}-${var.environment}-ecs-ml-s3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [

      {
        Sid    = "ListProjectDataBuckets"
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.bronze_bucket_name}",
          "arn:aws:s3:::${var.mlflow_artifact_bucket_name}",
          "arn:aws:s3:::${var.training_extracts_bucket_name}"
        ]
      },

      {
        Sid    = "ReadWriteProjectDataObjects"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "arn:aws:s3:::${var.bronze_bucket_name}/*",
          "arn:aws:s3:::${var.mlflow_artifact_bucket_name}/*",
          "arn:aws:s3:::${var.training_extracts_bucket_name}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "s3_data_access" {
  role       = aws_iam_role.task_role.name
  policy_arn = aws_iam_policy.s3_data_access.arn
}