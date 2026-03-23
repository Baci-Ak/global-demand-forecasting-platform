# ==============================================================================
# envs/prod/ecs-ml/variables.tf
# ==============================================================================
#
# Purpose
# - Inputs for the production ECS ML runtime stack.
# - Mirror the environment-level values that are passed into the reusable
#   ecs-ml-runtime module.
# - Keep naming, sizing, logging, and image configuration explicit.
# ==============================================================================

# ------------------------------------------------------------------------------
# Global environment identity
# ------------------------------------------------------------------------------

variable "project_name" {
  description = "Project identifier used for naming and tagging."
  type        = string
  default     = "gdf"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region for all resources in this environment."
  type        = string
  default     = "us-east-1"
}

# ------------------------------------------------------------------------------
# ECS ML runtime naming
# ------------------------------------------------------------------------------

variable "cluster_name" {
  description = "Name of the ECS cluster."
  type        = string
}

variable "execution_role_name" {
  description = "Name of the ECS task execution IAM role."
  type        = string
}

variable "log_group_name" {
  description = "CloudWatch log group name for ML runtime tasks."
  type        = string
}

variable "log_stream_prefix" {
  description = "CloudWatch log stream prefix for the container."
  type        = string
  default     = "ml-runtime"
}

variable "task_family" {
  description = "ECS task definition family name."
  type        = string
}

variable "container_name" {
  description = "Name of the main ML runtime container."
  type        = string
  default     = "ml-runtime"
}

# ------------------------------------------------------------------------------
# Runtime image
# ------------------------------------------------------------------------------

variable "ml_runtime_image" {
  description = "Full image URI for the production ML runtime container."
  type        = string
  default     = null
}

variable "create_task_definition" {
  description = "Whether to create the ECS task definition in this stack."
  type        = bool
  default     = false
}

# ------------------------------------------------------------------------------
# Runtime sizing
# ------------------------------------------------------------------------------

variable "task_cpu" {
  description = "Fargate task CPU units."
  type        = number
  default     = 2048
}

variable "task_memory" {
  description = "Fargate task memory in MiB."
  type        = number
  default     = 4096
}

# ------------------------------------------------------------------------------
# Observability
# ------------------------------------------------------------------------------

variable "log_retention_in_days" {
  description = "Retention period for CloudWatch logs."
  type        = number
  default     = 30
}

variable "container_insights_enabled" {
  description = "Whether ECS Container Insights should be enabled."
  type        = bool
  default     = true
}

# ------------------------------------------------------------------------------
# Tags
# ------------------------------------------------------------------------------

variable "tags" {
  description = "Additional tags applied to stack resources."
  type        = map(string)
  default     = {}
}