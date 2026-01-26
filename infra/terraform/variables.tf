/*
  File: variables.tf

  Purpose:
  - Declare input variables used across environments.
  - Keep variable definitions centralized so env folders stay small and readable.
*/

variable "project_name" {
  description = "Short project identifier used for naming and tagging."
  type        = string
  default     = "global-demand-forecasting"
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod)."
  type        = string
}

variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}
