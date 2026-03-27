# ==============================================================================
# envs/dev/s3/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose stack-level outputs for integration with other stacks.
# - These outputs are typically consumed via terraform_remote_state or CI/CD.
# ==============================================================================

output "bronze_bucket_name" {
  description = "Name of the dev bronze bucket."
  value       = module.bronze_bucket.bucket_name
}

output "bronze_bucket_arn" {
  description = "ARN of the dev bronze bucket."
  value       = module.bronze_bucket.bucket_arn
}

output "bronze_bucket_id" {
  description = "ID of the dev bronze bucket."
  value       = module.bronze_bucket.bucket_id
}




output "airflow_bucket_name" {
  description = "Name of the dev MWAA (Airflow runtime) bucket."
  value       = module.airflow_bucket.bucket_name
}

output "airflow_bucket_arn" {
  description = "ARN of the dev MWAA (Airflow runtime) bucket."
  value       = module.airflow_bucket.bucket_arn
}

output "airflow_bucket_id" {
  description = "ID of the dev MWAA (Airflow runtime) bucket."
  value       = module.airflow_bucket.bucket_id
}





output "mlflow_artifacts_bucket_name" {
  description = "Name of the production S3 bucket used for MLflow model and run artifacts."
  value       = module.mlflow_artifacts_bucket.bucket_name
}

output "mlflow_artifacts_bucket_arn" {
  description = "ARN of the production S3 bucket used for MLflow model and run artifacts."
  value       = module.mlflow_artifacts_bucket.bucket_arn
}

output "mlflow_artifacts_bucket_id" {
  description = "ID of the production S3 bucket used for MLflow model and run artifacts."
  value       = module.mlflow_artifacts_bucket.bucket_id
}


output "training_extracts_bucket_name" {
  description = "S3 bucket name for ML training extracts."
  value       = module.training_extracts_bucket.bucket_name
}



output "forecast_application_bucket_name" {
  description = "S3 bucket name for the forecast application snapshots."
  value       = module.forecast_application_bucket.bucket_name
}

output "forecast_application_bucket_arn" {
  description = "ARN of the S3 bucket used for forecast application snapshots."
  value       = module.forecast_application_bucket.bucket_arn
}

output "forecast_application_bucket_id" {
  description = "ID of the S3 bucket used for forecast application snapshots."
  value       = module.forecast_application_bucket.bucket_id
}