# ==============================================================================
# envs/prod/mlflow/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose production MLflow runtime coordinates for downstream stacks and tooling.
# ==============================================================================

output "service_name" {
  description = "Name of the ECS service running MLflow."
  value       = module.mlflow_service.service_name
}

output "task_definition_arn" {
  description = "ARN of the MLflow ECS task definition."
  value       = module.mlflow_service.task_definition_arn
}

output "execution_role_arn" {
  description = "ARN of the MLflow ECS execution role."
  value       = module.mlflow_service.execution_role_arn
}

output "task_role_arn" {
  description = "ARN of the MLflow ECS task role."
  value       = module.mlflow_service.task_role_arn
}

output "tracking_uri" {
  description = "Internal MLflow tracking URI."
  value       = module.mlflow_service.tracking_uri
}

output "alb_dns_name" {
  description = "Internal DNS name of the MLflow ALB."
  value       = module.mlflow_service.alb_dns_name
}

output "task_security_group_id" {
  description = "Security group id attached to MLflow ECS tasks."
  value       = module.mlflow_service.task_security_group_id
}

output "alb_security_group_id" {
  description = "Security group id attached to the MLflow internal ALB."
  value       = module.mlflow_service.alb_security_group_id
}