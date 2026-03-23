# ==============================================================================
# modules/mlflow-ecs-service/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose MLflow runtime coordinates to environment stacks and tooling.
# ==============================================================================

output "service_name" {
  description = "Name of the ECS service running MLflow."
  value       = aws_ecs_service.this.name
}

output "task_definition_arn" {
  description = "ARN of the MLflow ECS task definition."
  value       = aws_ecs_task_definition.this.arn
}

output "execution_role_arn" {
  description = "ARN of the MLflow ECS execution role."
  value       = aws_iam_role.execution.arn
}

output "task_role_arn" {
  description = "ARN of the MLflow ECS task role."
  value       = aws_iam_role.task.arn
}

output "alb_dns_name" {
  description = "Internal DNS name of the MLflow load balancer."
  value       = aws_lb.this.dns_name
}

output "tracking_uri" {
  description = "Internal MLflow tracking URI."
  value       = "http://${aws_lb.this.dns_name}:${var.container_port}"
}

output "task_security_group_id" {
  description = "Security group id attached to MLflow ECS tasks."
  value       = aws_security_group.task.id
}

output "alb_security_group_id" {
  description = "Security group id attached to the internal MLflow ALB."
  value       = aws_security_group.alb.id
}