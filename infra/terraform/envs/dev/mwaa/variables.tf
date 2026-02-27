# ==============================================================================
# envs/dev/mwaa/variables.tf
# ==============================================================================
#
# Purpose
# - Inputs for the dev MWAA stack.
# - Keep this file as the contract for what can be configured via terraform.tfvars.
# ==============================================================================

# ------------------------------------------------------------------------------
# Identity
# ------------------------------------------------------------------------------

variable "project_name" {
  description = "Project identifier used for tagging and resource naming."
  type        = string
  default     = "gdf"
}

variable "environment" {
  description = "Deployment environment name (e.g., dev, prod)."
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for all resources in this environment."
  type        = string
  default     = "us-east-1"
}

# ------------------------------------------------------------------------------
# MWAA core configuration
# ------------------------------------------------------------------------------

variable "airflow_version" {
  description = "MWAA Airflow version."
  type        = string
}

variable "environment_class" {
  description = "MWAA environment class."
  type        = string
}

variable "min_workers" {
  description = "Minimum number of MWAA workers."
  type        = number
}

variable "max_workers" {
  description = "Maximum number of MWAA workers."
  type        = number
}

variable "webserver_access_mode" {
  description = "MWAA webserver access mode: PRIVATE_ONLY or PUBLIC_ONLY."
  type        = string
  default     = "PRIVATE_ONLY"
}

variable "airflow_configuration_options" {
  description = "Airflow configuration overrides passed to MWAA."
  type        = map(string)
  default     = {}
}

# ------------------------------------------------------------------------------
# Source bucket (DAGs + optional artifacts)
# ------------------------------------------------------------------------------

variable "dag_s3_bucket" {
  description = "S3 bucket name holding Airflow DAGs and optional MWAA artifacts."
  type        = string
}

variable "dag_s3_path" {
  description = "S3 prefix for DAGs inside the bucket (no leading slash)."
  type        = string
  default     = "dags"
}

variable "requirements_s3_path" {
  description = "Optional S3 path to requirements.txt (relative to source bucket)."
  type        = string
  default     = null
}

variable "plugins_s3_path" {
  description = "Optional S3 path to plugins.zip (relative to source bucket)."
  type        = string
  default     = null
}

variable "startup_script_s3_path" {
  description = "Optional S3 path to startup script (relative to source bucket)."
  type        = string
  default     = null
}

# ------------------------------------------------------------------------------
# Logging configuration
# ------------------------------------------------------------------------------

variable "logging_configuration" {
  description = "Logging configuration for MWAA components."
  type = object({
    dag_processing = object({ enabled = bool, log_level = string })
    scheduler      = object({ enabled = bool, log_level = string })
    task           = object({ enabled = bool, log_level = string })
    webserver      = object({ enabled = bool, log_level = string })
    worker         = object({ enabled = bool, log_level = string })
  })
  default = {
    dag_processing = { enabled = true, log_level = "INFO" }
    scheduler      = { enabled = true, log_level = "INFO" }
    task           = { enabled = true, log_level = "INFO" }
    webserver      = { enabled = true, log_level = "INFO" }
    worker         = { enabled = true, log_level = "INFO" }
  }
}

# ------------------------------------------------------------------------------
# Webserver access controls (security group rules)
# ------------------------------------------------------------------------------

variable "allowed_web_cidr_blocks" {
  description = "CIDR blocks allowed to access the MWAA webserver (mainly for PUBLIC_ONLY)."
  type        = list(string)
  default     = []
}

variable "webserver_ingress_port" {
  description = "MWAA webserver ingress port."
  type        = number
  default     = 443
}

variable "webserver_ingress_protocol" {
  description = "MWAA webserver ingress protocol."
  type        = string
  default     = "tcp"
}

variable "enable_egress_all" {
  description = "If true, allow all egress from the MWAA security group."
  type        = bool
  default     = true
}


variable "cloudwatch_log_retention_days" {
  description = "CloudWatch log retention for MWAA log groups (days). Set via terraform.tfvars."
  type        = number
}







