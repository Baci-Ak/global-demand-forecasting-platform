# ==============================================================================
# modules/ecs-ml-runtime/main.tf
# ==============================================================================
#
# Purpose
# - Provision the shared ECS runtime foundation for ML jobs.
# - Create:
#   - ECS cluster
#   - task execution role
#   - CloudWatch log group
#   - base Fargate task definition
#
# Design principles
# - No hardcoded environment-specific values
# - Reusable across dev/prod and future ML jobs
# - Keep core runtime settings explicit via variables
# ==============================================================================

# ------------------------------------------------------------------------------
# ECS cluster
# ------------------------------------------------------------------------------


locals {
  create_task_definition = var.create_task_definition && var.ml_runtime_image != null
}



resource "aws_ecs_cluster" "this" {
  name = var.cluster_name

  setting {
    name  = "containerInsights"
    value = var.container_insights_enabled ? "enabled" : "disabled"
  }

  tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      component   = "ecs-ml-runtime"
      name        = var.cluster_name
    },
    var.tags
  )
}

# ------------------------------------------------------------------------------
# IAM: ECS task execution role
# - Allows ECS/Fargate to pull images and write logs.
# ------------------------------------------------------------------------------

data "aws_iam_policy_document" "ecs_task_execution_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "task_execution" {
  name               = var.execution_role_name
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume_role.json

  tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      component   = "ecs-ml-runtime"
      name        = var.execution_role_name
    },
    var.tags
  )
}

resource "aws_iam_role_policy_attachment" "ecs_execution_policy" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}



resource "aws_iam_role_policy" "execution_runtime_secrets" {
  name = "${var.project_name}-${var.environment}-ecs-ml-execution-runtime-secrets"
  role = aws_iam_role.task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadWarehouseDsnSecret"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          var.warehouse_dsn_secret_arn
        ]
      }
    ]
  })
}
# ------------------------------------------------------------------------------
# CloudWatch logs
# ------------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "this" {
  name              = var.log_group_name
  retention_in_days = var.log_retention_in_days

  tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      component   = "ecs-ml-runtime"
      name        = var.log_group_name
    },
    var.tags
  )
}

# ------------------------------------------------------------------------------
# ECS task definition
# - Base task definition for the ML runtime image.
# - Specific commands will be supplied later by ECS RunTask / Airflow.
# ------------------------------------------------------------------------------

resource "aws_ecs_task_definition" "this" {
  count = local.create_task_definition ? 1 : 0
  family                   = var.task_family
  requires_compatibilities = ["FARGATE"]

  cpu    = tostring(var.task_cpu)
  memory = tostring(var.task_memory)

  network_mode       = "awsvpc"
  execution_role_arn = aws_iam_role.task_execution.arn
  task_role_arn = aws_iam_role.task_role.arn

    container_definitions = jsonencode([
    {
      name      = var.container_name
      image     = var.ml_runtime_image
      essential = true

      environment = [
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "MLFLOW_TRACKING_URI"
          value = var.mlflow_tracking_uri
        },
        {
          name  = "TRAINING_EXTRACTS_BUCKET"
          value = var.training_extracts_bucket_name
        },
        {
          name  = "REDSHIFT_COPY_ROLE_ARN"
          value = var.redshift_copy_role_arn
        }
      ]

      secrets = [
        {
          name      = "WAREHOUSE_DSN"
          valueFrom = var.warehouse_dsn_secret_arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.this.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = var.log_stream_prefix
        }
      }
    }
  ])

  tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      component   = "ecs-ml-runtime"
      name        = var.task_family
    },
    var.tags
  )
}