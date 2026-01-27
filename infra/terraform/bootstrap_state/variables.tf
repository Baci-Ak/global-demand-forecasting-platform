/*
  Input variables for bootstrap stack.
*/

variable "project_name" {
  description = "Project identifier used in names/tags."
  type        = string
  default     = "global-demand-forecasting"
}

variable "environment" {
  description = "Environment name (e.g., dev, prod)."
  type        = string
}

variable "aws_region" {
  description = "AWS region for state resources."
  type        = string
  default     = "us-east-1"
}
