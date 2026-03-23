# ==============================================================================
# modules/mlflow-ecs-service/variables.tf
# ==============================================================================
#
# Purpose
# - Inputs for the reusable ECS-hosted MLflow service module.
# - Keep all runtime sizing, networking, naming, and secret wiring explicit.
# ==============================================================================

variable "project_name" {
  description = "Project identifier used for naming and tagging."
  type        = string
}

variable "environment" {
  description = "Deployment environment name (dev/prod)."
  type        = string
}

variable "aws_region" {
  description = "AWS region for logs and runtime resources."
  type        = string
}

# ------------------------------------------------------------------------------
# ECS cluster
# ------------------------------------------------------------------------------

variable "ecs_cluster_arn" {
  description = "ARN of the ECS cluster where MLflow will run."
  type        = string
}

# ------------------------------------------------------------------------------
# Networking
# ------------------------------------------------------------------------------

variable "vpc_id" {
  description = "VPC id where MLflow will run."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet ids for the MLflow ECS service."
  type        = list(string)
}

variable "allowed_ingress_security_group_ids" {
  description = "Security groups allowed to access the MLflow internal load balancer."
  type        = list(string)
  default     = []
}

variable "additional_task_security_group_ids" {
  description = "Additional security groups attached to the MLflow ECS task ENIs."
  type        = list(string)
  default     = []
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

variable "mlflow_backend_store_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the MLflow backend store URI."
  type        = string
}

variable "mlflow_artifact_bucket_name" {
  description = "S3 bucket name used for MLflow artifacts."
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
  description = "Additional tags applied to all module resources."
  type        = map(string)
  default     = {}
}