# ==============================================================================
# modules/mwaa/variables.tf
# ==============================================================================
#
# Purpose
# - Inputs for provisioning an Amazon MWAA environment.
# ==============================================================================



# ------------------------------------------------------------------------------
# Identity
# ------------------------------------------------------------------------------

variable "project_name" {
  description = "Project identifier used for tagging and resource naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment name (e.g., dev, prod)."
  type        = string
}

variable "tags" {
  description = "Additional tags to apply to all resources."
  type        = map(string)
  default     = {}
}

# ------------------------------------------------------------------------------
# MWAA core configuration
# ------------------------------------------------------------------------------

variable "airflow_version" {
  description = "MWAA Airflow version (e.g., 2.8.1)."
  type        = string
}

variable "environment_class" {
  description = "MWAA environment class (e.g., mw1.small, mw1.medium)."
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
  description = "Airflow configuration overrides for MWAA."
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
# Logging
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
# Networking / Security
# ------------------------------------------------------------------------------

variable "vpc_id" {
  description = "VPC id where MWAA will run."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet ids for MWAA (at least 2 in different AZs)."
  type        = list(string)
}

variable "allowed_web_sg_ids" {
  description = "Security groups allowed to access the MWAA webserver (PRIVATE_ONLY)."
  type        = list(string)
  default     = []
}

variable "allowed_web_cidr_blocks" {
  description = "CIDR blocks allowed to access the MWAA webserver (PUBLIC_ONLY)."
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



variable "additional_security_group_ids" {
  description = "Additional security groups to attach to MWAA environment ENIs (e.g., shared workloads SG)."
  type        = list(string)
  default     = []
}




variable "cloudwatch_log_retention_days" {
  description = "Retention (days) for MWAA CloudWatch Log Groups (DAGProcessing/Scheduler/Webserver/Worker/Task). Set per-environment in terraform.tfvars."
  type        = number

  validation {
    condition     = var.cloudwatch_log_retention_days >= 1
    error_message = "cloudwatch_log_retention_days must be >= 1."
  }
}





variable "requirements_s3_object_version" {
  description = "S3 VersionId for requirements.txt (required by MWAA when requirements_s3_path is set)."
  type        = string
  default     = null
}

variable "plugins_s3_object_version" {
  description = "S3 VersionId for plugins.zip (required by MWAA when plugins_s3_path is set)."
  type        = string
  default     = null
}

variable "startup_script_s3_object_version" {
  description = "S3 VersionId for startup script (required by MWAA when startup_script_s3_path is set)."
  type        = string
  default     = null
}







variable "data_bucket_names" {
  description = "Project data buckets (e.g., bronze) that MWAA tasks may read/write."
  type        = list(string)
  default     = []
}