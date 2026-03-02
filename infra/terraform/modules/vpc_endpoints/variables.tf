# ==============================================================================
# modules/vpc_endpoints/variables.tf
# ==============================================================================
#
# Purpose
# - Inputs for provisioning VPC endpoints required by private workloads.
#
# Notes
# - MWAA in private subnets often needs PrivateLink endpoints for reliable access
#   to AWS services (Logs/SQS/S3/KMS/CloudWatch).
# ==============================================================================

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

variable "aws_region" {
  description = "AWS region for endpoint service names."
  type        = string
}

variable "vpc_id" {
  description = "VPC id where endpoints will be created."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet ids that will host interface endpoints."
  type        = list(string)
}

variable "private_route_table_ids" {
  description = "Private route table ids used by gateway endpoints (e.g., S3)."
  type        = list(string)
}

variable "consumer_security_groups" {
  description = "Map of consumer SGs allowed to reach interface endpoints. Keys must be stable."
  type        = map(string)
  default     = {}
}


variable "enable_s3_gateway_endpoint" {
  description = "If true, create an S3 gateway endpoint for private route tables."
  type        = bool
  default     = true
}

variable "interface_endpoints" {
  description = "List of interface endpoint short names to create (e.g., logs, sqs, monitoring, kms)."
  type = list(string)
  default = [
    "logs",
    "sqs",
    "monitoring",
    "kms",
    "airflow.api",
    "airflow.env",
    "airflow.ops"
  ]
}

variable "enable_private_dns" {
  description = "If true, enable private DNS for interface endpoints (recommended)."
  type        = bool
  default     = true
}
