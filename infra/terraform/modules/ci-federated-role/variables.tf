# ==============================================================================
# modules/ci-federated-role/variables.tf
# ==============================================================================
#
# Purpose
# - Inputs for a reusable CI/CD federated IAM role module.
#
# Design
# - Keep identity-provider details parameterized.
# - Keep environment-specific names/ARNs outside the module.
# - Allow the same module to work for dev/prod and future CI providers.
# ==============================================================================

variable "role_name" {
  description = "Name of the IAM role to create for CI/CD federation."
  type        = string
}

variable "oidc_provider_arn" {
  description = "ARN of the IAM OIDC provider."
  type        = string
}

variable "oidc_audience" {
  description = "OIDC audience expected in the token."
  type        = string
  default     = "sts.amazonaws.com"
}

variable "oidc_subjects" {
  description = "Allowed OIDC subject patterns for assuming the role."
  type        = list(string)
}

variable "mwaa_environment_arn" {
  description = "ARN of the MWAA environment managed by this CI role."
  type        = string
}

variable "mwaa_execution_role_arn" {
  description = "ARN of the MWAA execution role managed by Terraform."
  type        = string
}

variable "terraform_lock_table_arn" {
  description = "ARN of the DynamoDB table used for Terraform state locking."
  type        = string
}

variable "cloudwatch_log_group_prefix" {
  description = "CloudWatch Logs log-group prefix for the MWAA environment, without trailing wildcard."
  type        = string
}

variable "tags" {
  description = "Tags to apply to the IAM role."
  type        = map(string)
  default     = {}
}

variable "mwaa_bucket_arn" {
  description = "ARN of the MWAA S3 bucket used for DAG and runtime artifact deployment."
  type        = string
}

variable "mwaa_bucket_objects_arn" {
  description = "ARN pattern for objects inside the MWAA S3 bucket."
  type        = string
}