# ==============================================================================
# envs/prod/mlflow/variables.tf
# ==============================================================================
#
# Purpose
# - Inputs for the production MLflow ECS service stack.
# - Keep naming, sizing, image, and secret configuration explicit.
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
# Naming
# ------------------------------------------------------------------------------

variable "service_name" {
  description = "Logical service name for MLflow."
  type        = string
}

variable "task_family" {
  description = "ECS task definition family name."
  type        = string
}

variable "execution_role_name" {
  description = "IAM role name for the ECS task execution role."
  type        = string
}

variable "task_role_name" {
  description = "IAM role name for the ECS task runtime role."
  type        = string
}

variable "log_group_name" {
  description = "CloudWatch log group name for MLflow."
  type        = string
}

variable "log_stream_prefix" {
  description = "CloudWatch log stream prefix for MLflow container logs."
  type        = string
  default     = "mlflow"
}

# ------------------------------------------------------------------------------
# Container runtime
# ------------------------------------------------------------------------------

variable "mlflow_image" {
  description = "Full container image URI for the MLflow service."
  type        = string
}

variable "container_name" {
  description = "Name of the MLflow container."
  type        = string
  default     = "mlflow"
}

variable "container_port" {
  description = "Container port exposed by the MLflow service."
  type        = number
  default     = 5000
}

variable "desired_count" {
  description = "Desired number of MLflow ECS tasks."
  type        = number
  default     = 1
}

variable "task_cpu" {
  description = "Fargate task CPU units."
  type        = number
  default     = 1024
}

variable "task_memory" {
  description = "Fargate task memory in MiB."
  type        = number
  default     = 2048
}

variable "health_check_path" {
  description = "ALB health check path for MLflow."
  type        = string
  default     = "/"
}

# ------------------------------------------------------------------------------
# MLflow configuration
# ------------------------------------------------------------------------------

variable "mlflow_backend_store_secret_id" {
  description = "Secrets Manager secret name containing the MLflow backend store URI."
  type        = string
}

# ------------------------------------------------------------------------------
# Logging / observability
# ------------------------------------------------------------------------------

variable "log_retention_in_days" {
  description = "Retention period for CloudWatch logs."
  type        = number
  default     = 30
}

# ------------------------------------------------------------------------------
# Tags
# ------------------------------------------------------------------------------

variable "tags" {
  description = "Additional tags applied to stack resources."
  type        = map(string)
  default     = {}
}