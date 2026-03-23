# ==============================================================================
# modules/ecs-ml-runtime/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose identifiers needed by environment stacks and orchestration layers.
# ==============================================================================

output "ecs_cluster_name" {
  description = "Name of the ECS cluster."
  value       = aws_ecs_cluster.this.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster."
  value       = aws_ecs_cluster.this.arn
}

output "task_definition_family" {
  description = "Family name of the ECS task definition."
  value       = local.create_task_definition ? aws_ecs_task_definition.this[0].family : null
}

output "task_definition_arn" {
  description = "ARN of the ECS task definition."
  value       = local.create_task_definition ? aws_ecs_task_definition.this[0].arn : null
}

output "task_execution_role_arn" {
  description = "ARN of the ECS task execution role."
  value       = aws_iam_role.task_execution.arn
}

output "log_group_name" {
  description = "CloudWatch log group name for ML runtime tasks."
  value       = aws_cloudwatch_log_group.this.name
}


output "task_role_arn" {
  description = "IAM role used by the ML runtime container at execution time."
  value       = aws_iam_role.task_role.arn
}