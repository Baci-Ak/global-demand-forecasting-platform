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
