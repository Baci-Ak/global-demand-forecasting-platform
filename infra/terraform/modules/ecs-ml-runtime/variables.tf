# ==============================================================================
# modules/ecs-ml-runtime/variables.tf
# ==============================================================================
#
# Purpose
# - Inputs for the reusable ECS ML runtime module.
# - Keep all runtime sizing, naming, and logging explicit and environment-safe.
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

variable "task_family" {
  description = "ECS task definition family name."
  type        = string
}

variable "container_name" {
  description = "Name of the main ML runtime container."
  type        = string
  default     = "ml-runtime"
}

variable "ml_runtime_image" {
  description = "Full container image URI for the ML runtime."
  type        = string
  default     = null
}

variable "task_cpu" {
  description = "Fargate task CPU units."
  type        = number
  default     = 4096
}

variable "task_memory" {
  description = "Fargate task memory in MiB."
  type        = number
  default     = 16384
}

variable "tags" {
  description = "Additional tags applied to all module resources."
  type        = map(string)
  default     = {}
}



variable "warehouse_dsn_secret_arn" {
  description = "Secrets Manager ARN for the warehouse DSN injected into the ML runtime container."
  type        = string
}

variable "mlflow_tracking_uri" {
  description = "MLflow tracking URI injected into the ML runtime container."
  type        = string
}



variable "create_task_definition" {
  description = "Whether to create the ECS task definition."
  type        = bool
  default     = false
}

variable "mlflow_artifact_bucket_name" {
  description = "Actual S3 bucket name used by MLflow for artifacts."
  type        = string
}


variable "training_extracts_bucket_name" {
  description = "S3 bucket name for ML training extracts."
  type        = string
}


variable "bronze_bucket_name" {
  description = "S3 bucket name for Bronze data."
  type        = string
}

variable "redshift_copy_role_arn" {
  description = "IAM role ARN used by Redshift UNLOAD/COPY to access S3."
  type        = string
}