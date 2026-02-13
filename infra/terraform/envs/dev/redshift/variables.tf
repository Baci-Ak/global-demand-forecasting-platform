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
