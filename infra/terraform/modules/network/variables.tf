# ==============================================================================
# modules/network/variables.tf
# ==============================================================================
#
# Purpose
# - Declare inputs for the reusable network module.
#
# Notes
# - This module will provision a VPC with public/private subnets across multiple
#   availability zones, suitable for RDS and other managed services.
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
# Network design inputs
# ------------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones to spread subnets across."
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "availability_zones must include at least 2 AZs."
  }
}

variable "single_nat_gateway" {
  description = "If true, provision a single NAT Gateway shared across private subnets."
  type        = bool
  default     = true
}
