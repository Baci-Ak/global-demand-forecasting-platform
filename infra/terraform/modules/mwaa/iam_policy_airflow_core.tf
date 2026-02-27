# ==============================================================================
# modules/mwaa/iam_policy_airflow_core.tf
# ==============================================================================
#
# Purpose
# - Attach baseline IAM permissions to the MWAA execution role so the environment
#   can run DAGs reliably:
#   - Publish Airflow metrics
#   - Read DAGs/artifacts from S3 (MWAA source bucket)
#   - Use SQS queues (Celery executor)
#   - Write/read CloudWatch Logs
#   - Use KMS via AWS services (SQS/S3/CloudWatch Logs)
#
# Design notes
# - VPC/EC2 permissions are intentionally separated into iam_policy_vpc_networking.tf.
# - CloudWatch Logs permissions are split into WRITE and READ policies for clarity.
# - KMS permissions are scoped to "via service" usage (SQS/S3/Logs), which matches
#   how MWAA interacts with encryption in managed services.
#
# Operational note
# - If a customer-managed KMS key (CMK) is used, the CMK key policy must also allow
#   this role. Identity policy alone is not sufficient if the key policy denies.
# ==============================================================================

# ------------------------------------------------------------------------------
# Core permissions (Airflow metrics, S3 DAG access, CloudWatch metrics, SQS, KMS)
# ------------------------------------------------------------------------------
resource "aws_iam_role_policy" "mwaa_airflow_core" {
  name = "${local.name_prefix}-airflow-core"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # ------------------------------------------------------------------------
      # MWAA metrics publishing (Airflow service API)
      # ------------------------------------------------------------------------
      {
        Sid    = "AirflowPublishMetrics"
        Effect = "Allow"
        Action = ["airflow:PublishMetrics"]
        Resource = [
          "arn:aws:airflow:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:environment/${local.name_prefix}"
        ]
      },

      # ------------------------------------------------------------------------
      # S3: read DAGs (and optional artifacts) from the MWAA source bucket
      # ------------------------------------------------------------------------
      {
        Sid    = "S3ReadDagBucket"
        Effect = "Allow"
        Action = [
          "s3:GetObject*",
          "s3:GetBucket*",
          "s3:List*"
        ]
        Resource = [
          "arn:aws:s3:::${var.dag_s3_bucket}",
          "arn:aws:s3:::${var.dag_s3_bucket}/*"
        ]
      },

      # ------------------------------------------------------------------------
      # S3: read/write data buckets (bronze, artifacts, etc.)
      # - decoupled from MWAA source bucket
      # ------------------------------------------------------------------------
      {
        Sid    = "S3ReadWriteDataBucketsObjects"
        Effect = "Allow"
        Action = [
          "s3:GetObject*",
          "s3:PutObject",
          "s3:AbortMultipartUpload",
          "s3:ListMultipartUploadParts",
          "s3:ListBucketMultipartUploads"
        ]
        Resource = [
          for b in var.data_bucket_names : "arn:aws:s3:::${b}/*"
        ]
      },
      {
        Sid    = "S3ListDataBuckets"
        Effect = "Allow"
        Action = ["s3:ListBucket"]
        Resource = [
          for b in var.data_bucket_names : "arn:aws:s3:::${b}"
        ]
      },

      # MWAA performs public access block validation checks as part of bucket use.
      {
        Sid      = "S3AccountPublicAccessBlockRead"
        Effect   = "Allow"
        Action   = ["s3:GetAccountPublicAccessBlock"]
        Resource = ["*"]
      },
      {
        Sid      = "S3BucketPublicAccessBlockRead"
        Effect   = "Allow"
        Action   = ["s3:GetBucketPublicAccessBlock"]
        Resource = ["arn:aws:s3:::${var.dag_s3_bucket}"]
      },

      # ------------------------------------------------------------------------
      # CloudWatch custom metrics (PutMetricData does not support resource scoping)
      # ------------------------------------------------------------------------
      {
        Sid      = "CloudWatchPutMetricData"
        Effect   = "Allow"
        Action   = ["cloudwatch:PutMetricData"]
        Resource = ["*"]
      },

      # ------------------------------------------------------------------------
      # SQS: internal Celery queues used by MWAA (airflow-celery-*)
      # ------------------------------------------------------------------------
      {
        Sid    = "SqsForAirflow"
        Effect = "Allow"
        Action = [
          "sqs:ChangeMessageVisibility",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl",
          "sqs:ReceiveMessage",
          "sqs:SendMessage"
        ]
        Resource = [
          "arn:aws:sqs:${data.aws_region.current.name}:*:airflow-celery-*"
        ]
      },

      # ------------------------------------------------------------------------
      # KMS: allow data key generation/encrypt/decrypt when called via AWS services
      #
      # Why this exists:
      # - MWAA Celery uses SQS; if the queue is KMS-encrypted, SendMessage triggers
      #   KMS GenerateDataKey on the queue's key.
      # - MWAA can also touch KMS indirectly via S3 (source bucket) and CloudWatch Logs.
      # ------------------------------------------------------------------------
      {
        Sid    = "KmsViaAwsServices"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:Encrypt",
          "kms:GenerateDataKey",
          "kms:GenerateDataKeyWithoutPlaintext"
        ]
        Resource = ["*"]
        Condition = {
          StringEquals = {
            "kms:CallerAccount" = "${data.aws_caller_identity.current.account_id}"
          }
          StringLike = {
            "kms:ViaService" = [
              "sqs.${data.aws_region.current.name}.amazonaws.com",
              "s3.${data.aws_region.current.name}.amazonaws.com",
              "logs.${data.aws_region.current.name}.amazonaws.com"
            ]
          }
        }
      }
    ]
  })
}

# ------------------------------------------------------------------------------
# CloudWatch Logs - WRITE permissions
#
# Used by: scheduler, workers, tasks, DAG processor
# ------------------------------------------------------------------------------
resource "aws_iam_role_policy" "mwaa_cloudwatch_write" {
  name = "${local.name_prefix}-cloudwatch-write"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogsWriteAirflowLogGroups"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:airflow-*",
          "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:airflow-*:log-stream:*"
        ]
      }
    ]
  })
}

# ------------------------------------------------------------------------------
# CloudWatch Logs - READ permissions
#
# Used by: webserver UI (to display logs)
# ------------------------------------------------------------------------------
resource "aws_iam_role_policy" "mwaa_cloudwatch_read" {
  name = "${local.name_prefix}-cloudwatch-read"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogsReadForAirflowUI"
        Effect = "Allow"
        Action = [
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:GetLogEvents",
          "logs:FilterLogEvents",
          "logs:GetLogRecord",
          "logs:GetLogGroupFields",
          "logs:GetQueryResults",
          "logs:StartQuery",
          "logs:StopQuery"
        ]
        Resource = [
          "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:airflow-*",
          "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:airflow-*:log-stream:*"
        ]
      }
    ]
  })
}
