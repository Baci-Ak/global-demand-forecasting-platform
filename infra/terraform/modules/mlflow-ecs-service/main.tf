# ==============================================================================
# modules/mlflow-ecs-service/main.tf
# ==============================================================================
#
# Purpose
# - Run MLflow as a private ECS/Fargate service behind an internal ALB.
# - Use:
#   - RDS/Postgres backend store (via Secrets Manager)
#   - S3 artifact store
#
# Design principles
# - No hardcoded environment-specific values
# - Private-only access
# - Reusable across environments
# - Explicit IAM and networking
# ==============================================================================

locals {
  name_prefix   = "${var.project_name}-${var.environment}-${var.service_name}"
  artifact_root = "s3://${var.mlflow_artifact_bucket_name}"
}

# ------------------------------------------------------------------------------
# Security group: internal ALB
# ------------------------------------------------------------------------------

resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg"
  description = "Security group for internal MLflow ALB."
  vpc_id      = var.vpc_id

  tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      component   = "mlflow"
      name        = "${local.name_prefix}-alb-sg"
    },
    var.tags
  )
}

resource "aws_security_group_rule" "alb_ingress_from_allowed_sgs" {
  for_each = toset(var.allowed_ingress_security_group_ids)

  type                     = "ingress"
  security_group_id        = aws_security_group.alb.id
  from_port                = var.container_port
  to_port                  = var.container_port
  protocol                 = "tcp"
  source_security_group_id = each.value
  description              = "Allow internal access to MLflow from approved security groups."
}

resource "aws_security_group_rule" "alb_egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.alb.id
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow ALB outbound traffic."
}

# ------------------------------------------------------------------------------
# Security group: ECS tasks
# ------------------------------------------------------------------------------

resource "aws_security_group" "task" {
  name        = "${local.name_prefix}-task-sg"
  description = "Security group for MLflow ECS tasks."
  vpc_id      = var.vpc_id

  tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      component   = "mlflow"
      name        = "${local.name_prefix}-task-sg"
    },
    var.tags
  )
}

resource "aws_security_group_rule" "task_ingress_from_alb" {
  type                     = "ingress"
  security_group_id        = aws_security_group.task.id
  from_port                = var.container_port
  to_port                  = var.container_port
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
  description              = "Allow internal ALB to reach MLflow container."
}

resource "aws_security_group_rule" "task_egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.task.id
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow MLflow task outbound traffic."
}

# ------------------------------------------------------------------------------
# Internal ALB
# ------------------------------------------------------------------------------

resource "aws_lb" "this" {
  name               = substr(replace("${local.name_prefix}-alb", "_", "-"), 0, 32)
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.private_subnet_ids

  tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      component   = "mlflow"
      name        = "${local.name_prefix}-alb"
    },
    var.tags
  )
}

resource "aws_lb_target_group" "this" {
  name        = substr(replace("${local.name_prefix}-tg", "_", "-"), 0, 32)
  port        = var.container_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    enabled             = true
    path                = var.health_check_path
    matcher             = "200-399"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
  }

  tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      component   = "mlflow"
      name        = "${local.name_prefix}-tg"
    },
    var.tags
  )
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = var.container_port
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
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
      component   = "mlflow"
      name        = var.log_group_name
    },
    var.tags
  )
}

# ------------------------------------------------------------------------------
# IAM: ECS execution role
# ------------------------------------------------------------------------------

data "aws_iam_policy_document" "execution_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "execution" {
  name               = var.execution_role_name
  assume_role_policy = data.aws_iam_policy_document.execution_assume_role.json

  tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      component   = "mlflow"
      name        = var.execution_role_name
    },
    var.tags
  )
}

resource "aws_iam_role_policy_attachment" "execution_default" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "execution_secrets_read" {
  name = "${local.name_prefix}-execution-secrets-read"
  role = aws_iam_role.execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadMlflowBackendStoreSecret"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          var.mlflow_backend_store_secret_arn
        ]
      }
    ]
  })
}

# ------------------------------------------------------------------------------
# IAM: ECS task role
# ------------------------------------------------------------------------------

resource "aws_iam_role" "task" {
  name               = var.task_role_name
  assume_role_policy = data.aws_iam_policy_document.execution_assume_role.json

  tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      component   = "mlflow"
      name        = var.task_role_name
    },
    var.tags
  )
}

resource "aws_iam_role_policy" "task_s3_access" {
  name = "${local.name_prefix}-task-s3-access"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ListMlflowArtifactBucket"
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.mlflow_artifact_bucket_name}"
        ]
      },
      {
        Sid    = "ReadWriteMlflowArtifacts"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:AbortMultipartUpload",
          "s3:ListBucketMultipartUploads",
          "s3:ListMultipartUploadParts"
        ]
        Resource = [
          "arn:aws:s3:::${var.mlflow_artifact_bucket_name}/*"
        ]
      }
    ]
  })
}

# ------------------------------------------------------------------------------
# ECS task definition
# ------------------------------------------------------------------------------

resource "aws_ecs_task_definition" "this" {
  family                   = var.task_family
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  cpu    = tostring(var.task_cpu)
  memory = tostring(var.task_memory)

  execution_role_arn = aws_iam_role.execution.arn
  task_role_arn      = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = var.container_name
      image     = var.mlflow_image
      essential = true

      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "MLFLOW_DEFAULT_ARTIFACT_ROOT"
          value = local.artifact_root
        }
      ]

      secrets = [
        {
          name      = "MLFLOW_BACKEND_STORE_URI"
          valueFrom = var.mlflow_backend_store_secret_arn
        }
      ]

      entryPoint = ["sh", "-c"]
      command = [
        "mlflow server --host 0.0.0.0 --port ${var.container_port} --backend-store-uri \"$MLFLOW_BACKEND_STORE_URI\" --artifacts-destination \"${local.artifact_root}\""
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
      component   = "mlflow"
      name        = var.task_family
    },
    var.tags
  )
}

# ------------------------------------------------------------------------------
# ECS service
# ------------------------------------------------------------------------------

resource "aws_ecs_service" "this" {
  name            = var.service_name
  cluster         = var.ecs_cluster_arn
  task_definition = aws_ecs_task_definition.this.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200
  enable_execute_command             = true

  network_configuration {
    subnets          = var.private_subnet_ids
    assign_public_ip = false
    security_groups = concat(
      [aws_security_group.task.id],
      var.additional_task_security_group_ids
    )
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this.arn
    container_name   = var.container_name
    container_port   = var.container_port
  }

  depends_on = [aws_lb_listener.http]

  tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      component   = "mlflow"
      name        = var.service_name
    },
    var.tags
  )
}