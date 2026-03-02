# ==============================================================================
# modules/redshift-serverless/variables.tf
# ==============================================================================
#
# Purpose
# - Inputs for provisioning a Redshift Serverless namespace + workgroup.
# ==============================================================================

variable "project_name" {
  description = "Project identifier used for tagging and resource naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment name (dev/prod)."
  type        = string
}

variable "database_name" {
  description = "Default database name created in the Redshift namespace."
  type        = string
}

variable "admin_username" {
  description = "Admin username for Redshift."
  type        = string
}

variable "admin_password" {
  description = "Admin password for Redshift."
  type        = string
  sensitive   = true
}

variable "base_capacity" {
  description = "Redshift Serverless base capacity in RPUs."
  type        = number
}

variable "vpc_id" {
  description = "VPC id for network placement."
  type        = string
}

variable "subnet_ids" {
  description = "Subnets for the Redshift workgroup (private subnets recommended)."
  type        = list(string)
}

variable "allowed_sg_ids" {
  description = "Security groups allowed to connect to Redshift (e.g., jumphost SG)."
  type        = list(string)
}

variable "port" {
  description = "Redshift port."
  type        = number
  default     = 5439
}







# ------------------------------------------------------------------------------
# Cost guardrails (Serverless usage limits)
# ------------------------------------------------------------------------------

variable "enable_usage_limits" {
  description = "If true, apply Redshift Serverless usage limits to prevent runaway cost."
  type        = bool
  default     = true
}

variable "usage_limit_rpu_hours_per_day" {
  description = "Max RPU-hours per day for the workgroup. Null disables this limit."
  type        = number
  default     = null
}

variable "usage_limit_rpu_hours_per_week" {
  description = "Max RPU-hours per week for the workgroup. Null disables this limit."
  type        = number
  default     = null
}

variable "usage_limit_rpu_hours_per_month" {
  description = "Max RPU-hours per month for the workgroup. Null disables this limit."
  type        = number
  default     = null
}

variable "usage_limit_breach_action" {
  description = "Action when limit is breached. Valid values: 'log' or 'deactivate'."
  type        = string
  default     = "log"

  validation {
    condition     = contains(["log", "deactivate"], var.usage_limit_breach_action)
    error_message = "usage_limit_breach_action must be 'log' or 'deactivate'."
  }
}



# ------------------------------------------------------------------------------
# Logging (CloudWatch log exports)
# ------------------------------------------------------------------------------

variable "enable_log_exports" {
  description = "Enable Redshift Serverless CloudWatch log exports."
  type        = bool
  default     = true
}
