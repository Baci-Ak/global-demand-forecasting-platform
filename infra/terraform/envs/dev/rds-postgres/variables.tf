# ==============================================================================
# envs/dev/rds-postgres/variables.tf
# ==============================================================================
#
# Purpose
# - Inputs for the dev RDS Postgres stack.
# - Values are set via terraform.tfvars (no secrets in repo).
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


# ------------------------------------------------------------------------------
# Database identity (dev)
# ------------------------------------------------------------------------------

variable "db_name" {
  description = "Initial database name to create."
  type        = string
  default     = "gdf_audit"
}

variable "db_username" {
  description = "Master username for the database."
  type        = string
  default     = "gdf_admin"
}





# ------------------------------------------------------------------------------
# RDS configuration (dev)
# ------------------------------------------------------------------------------

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
  description = "Whether the DB should have a public endpoint."
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Prevents accidental deletion of the DB instance."
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot on destroy (dev convenience; set false in prod)."
  type        = bool
  default     = true
}


variable "db_port" {
  description = "Database port."
  type        = number
  default     = 5432
}
