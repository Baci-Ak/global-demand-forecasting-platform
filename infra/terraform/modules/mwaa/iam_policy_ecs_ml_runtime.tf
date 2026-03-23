# ==============================================================================
# modules/mwaa/iam_policy_ecs_ml_runtime.tf
# ==============================================================================
#
# Purpose
# - Allow MWAA to trigger ECS ML runtime tasks.
# - This enables Airflow DAGs in MWAA to run the production ML container on ECS.
#
# Scope
# - Run ECS tasks on the ML runtime cluster
# - Pass the ECS execution role and ECS task role to the task
#
# Design principles
# - Least privilege
# - Explicitly scoped to the production ECS ML runtime resources
# ==============================================================================

resource "aws_iam_role_policy" "mwaa_ecs_ml_runtime" {
  count = (
    var.ecs_ml_cluster_arn != null &&
    var.ecs_ml_task_definition_arn != null &&
    var.ecs_ml_task_role_arn != null
  ) ? 1 : 0

  name = "${local.name_prefix}-ecs-ml-runtime"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "RunEcsMlTasks"
        Effect = "Allow"
        Action = [
          "ecs:RunTask"
        ]
        Resource = [
          var.ecs_ml_task_definition_arn
        ]
        Condition = {
          ArnEquals = {
            "ecs:cluster" = var.ecs_ml_cluster_arn
          }
        }
      },
      {
        Sid    = "DescribeEcsMlTasks"
        Effect = "Allow"
        Action = [
          "ecs:DescribeTasks",
          "ecs:DescribeTaskDefinition"
        ]
        Resource = "*"
      },
      {
        Sid    = "PassEcsMlRoles"
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = [
          var.ecs_ml_task_role_arn,
          var.ecs_ml_execution_role_arn
        ]
      }
    ]
  })
}