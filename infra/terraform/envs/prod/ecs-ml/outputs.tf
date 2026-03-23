# ==============================================================================
# envs/prod/ecs-ml/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose ECS ML runtime coordinates to other Terraform stacks and tooling.
# - These values are consumed via terraform_remote_state by:
#     - monitoring
#     - future batch job orchestration
#     - CI/CD workflows
# ==============================================================================

# ------------------------------------------------------------------------------
# ECS cluster
# ------------------------------------------------------------------------------

output "ecs_cluster_name" {
  description = "Name of the ECS cluster running ML runtime jobs."
  value       = module.ecs_ml_runtime.ecs_cluster_name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster running ML runtime jobs."
  value       = module.ecs_ml_runtime.ecs_cluster_arn
}

# ------------------------------------------------------------------------------
# Task definition
# ------------------------------------------------------------------------------

output "task_definition_family" {
  description = "Family name of the ECS ML runtime task definition."
  value       = module.ecs_ml_runtime.task_definition_family
}

output "task_definition_arn" {
  description = "ARN of the ECS ML runtime task definition."
  value       = module.ecs_ml_runtime.task_definition_arn
}

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------

output "log_group_name" {
  description = "CloudWatch log group used by ML runtime tasks."
  value       = module.ecs_ml_runtime.log_group_name
}

# ------------------------------------------------------------------------------
# Execution role
# ------------------------------------------------------------------------------

output "task_execution_role_arn" {
  description = "IAM role used by ECS tasks to pull images and write logs."
  value       = module.ecs_ml_runtime.task_execution_role_arn
}




output "task_role_arn" {
  description = "ARN of the ECS ML runtime task role."
  value       = module.ecs_ml_runtime.task_role_arn
}