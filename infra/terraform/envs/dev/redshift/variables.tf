# ==============================================================================
# envs/dev/redshift/variables.tf
# ==============================================================================
#
# Purpose
# - Inputs for the dev Redshift stack.
# ==============================================================================

variable "project_name" {
  description = "Project identifier used for tagging and resource naming."
  type        = string
  default     = "gdf"
}

variable "environment" {
  description = "Deployment environment name (dev/prod)."
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for all resources in this environment."
  type        = string
  default     = "us-east-1"
}

variable "database_name" {
  description = "Default database name created in the Redshift namespace."
  type        = string
  default     = "warehouse"
}

variable "admin_username" {
  description = "Admin username for Redshift."
  type        = string
  default     = "admin"
}

variable "base_capacity" {
  description = "Redshift Serverless base capacity in RPUs (dev default)."
  type        = number
  default     = 8
}

variable "port" {
  description = "Redshift port."
  type        = number
  default     = 5439
}





# ------------------------------------------------------------------------------
# Cost guardrails (dev)
# ------------------------------------------------------------------------------

variable "enable_usage_limits" {
  description = "Enable Redshift Serverless usage limits."
  type        = bool
  default     = true
}

variable "usage_limit_rpu_hours_per_day" {
  description = "Daily RPU-hours cap (null disables)."
  type        = number
  default     = null
}

variable "usage_limit_rpu_hours_per_week" {
  description = "Weekly RPU-hours cap (null disables)."
  type        = number
  default     = null
}

variable "usage_limit_rpu_hours_per_month" {
  description = "Monthly RPU-hours cap (null disables)."
  type        = number
  default     = 200
}

variable "usage_limit_breach_action" {
  description = "Breach action: 'log' (dev) or 'deactivate' (prod)."
  type        = string
  default     = "log"
}

variable "enable_log_exports" {
  description = "Enable Redshift Serverless user activity logging."
  type        = bool
  default     = true
}