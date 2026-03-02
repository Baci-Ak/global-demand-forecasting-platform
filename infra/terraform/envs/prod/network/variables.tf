# ==============================================================================
# envs/dev/network/variables.tf
# ==============================================================================
#
# Purpose
# - Inputs for the dev network stack.
# - Values are set via terraform.tfvars (no secrets).
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
# VPC design inputs (dev)
# ------------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the dev VPC."
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones to spread subnets across."
  type        = list(string)
}

variable "single_nat_gateway" {
  description = "If true, provision a single NAT Gateway shared across private subnets (cost-conscious dev default)."
  type        = bool
  default     = true
}
