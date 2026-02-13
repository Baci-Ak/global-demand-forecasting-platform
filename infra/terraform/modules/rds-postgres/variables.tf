# ==============================================================================
# modules/rds-postgres/variables.tf
# ==============================================================================
#
# Purpose
# - Declare inputs for the reusable RDS Postgres module.
#
# Notes
# - This module will provision database infrastructure only.
# - Database credentials must not be hardcoded or committed in tfvars.
# ==============================================================================

variable "project_name" {
  description = "Project identifier used for tagging and resource naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment name (dev/prod)."
  type        = string
}


# ------------------------------------------------------------------------------
# Networking inputs
# ------------------------------------------------------------------------------

variable "vpc_id" {
  description = "VPC ID where the database will be deployed."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the DB subnet group."
  type        = list(string)
}


variable "trusted_source_sg_id" {
  description = "Optional security group ID allowed to connect to Postgres (e.g., SSM jump host SG)."
  type        = string
  default     = null
}


# ------------------------------------------------------------------------------
# Database configuration
# ------------------------------------------------------------------------------

variable "db_name" {
  description = "Initial database name to create."
  type        = string
}

variable "master_username" {
  description = "Master username for the database."
  type        = string
}

variable "master_password" {
  description = "Master password for the database (sourced from Secrets Manager by the caller)."
  type        = string
  sensitive   = true
}

variable "engine_version" {
  description = "PostgreSQL engine version."
  type        = string
  default     = "16.3"
}

variable "instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t4g.micro"
}

variable "allocated_storage_gb" {
  description = "Allocated storage in GB."
  type        = number
  default     = 20
}

variable "backup_retention_days" {
  description = "Number of days to retain automated backups."
  type        = number
  default     = 7
}

variable "publicly_accessible" {
  description = "Whether the DB should have a public endpoint (should be false for production)."
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Prevents accidental deletion of the DB instance."
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot on destroy (dev convenience; use false in prod)."
  type        = bool
  default     = true
}


variable "db_port" {
  description = "Database port."
  type        = number
  default     = 5432
}
