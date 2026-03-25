# ==============================================================================
# envs/dev/s3/main.tf
# ==============================================================================
#
# Purpose
# - Deploy the dev S3 bucket required for the project.
# - Keep "bronze" for data only and add a dedicated "airflow" bucket for MWAA runtime.

# Notes
# - Bucket names must be globally unique.
# - This stack provisions the bucket and baseline security controls.
#   Access policies are handled separately via IAM.
# ==============================================================================

data "aws_caller_identity" "current" {}

locals {
  bucket_name_suffix = data.aws_caller_identity.current.account_id

  bronze_bucket_name           = "${var.project_name}-${var.environment}-bronze-${local.bucket_name_suffix}"
  airflow_bucket_name          = "${var.project_name}-${var.environment}-airflow-${local.bucket_name_suffix}"
  mlflow_artifacts_bucket_name = "${var.project_name}-${var.environment}-mlflow-artifacts-${local.bucket_name_suffix}"
  training_extracts_bucket_name = "${var.project_name}-${var.environment}-training-extracts-${local.bucket_name_suffix}"
  forecast_application_bucket_name = "${var.project_name}-${var.environment}-forecast-application-${local.bucket_name_suffix}"
}





module "bronze_bucket" {
  source = "../../../modules/s3"

  project_name = var.project_name
  environment  = var.environment

  bucket_name       = local.bronze_bucket_name
  enable_versioning = var.enable_versioning

  sse_algorithm = var.s3_sse_algorithm
  force_destroy = var.s3_force_destroy

  tags = merge(var.s3_bucket_tags, {
    purpose   = "data-lake"
    data_zone = "bronze"
  })

  # Cost controls (dev defaults)
  enable_lifecycle                  = var.bronze_enable_lifecycle
  lifecycle_abort_multipart_days    = var.bronze_lifecycle_abort_multipart_days
  lifecycle_transition_ia_days      = var.bronze_lifecycle_transition_ia_days
  lifecycle_transition_glacier_days = var.bronze_lifecycle_transition_glacier_days

  # Dev retention 
  lifecycle_expire_days            = var.bronze_lifecycle_expire_days
  lifecycle_noncurrent_expire_days = var.bronze_lifecycle_noncurrent_expire_days
}

module "airflow_bucket" {
  source = "../../../modules/s3"

  project_name = var.project_name
  environment  = var.environment

  bucket_name       = local.airflow_bucket_name
  enable_versioning = var.enable_versioning

  sse_algorithm = var.s3_sse_algorithm
  force_destroy = var.s3_force_destroy

  tags = {
    component = "mwaa"
    purpose   = "airflow-runtime"
  }
}




module "mlflow_artifacts_bucket" {
  source = "../../../modules/s3"

  project_name = var.project_name
  environment  = var.environment

  bucket_name       = local.mlflow_artifacts_bucket_name
  enable_versioning = var.enable_versioning

  sse_algorithm = var.s3_sse_algorithm
  force_destroy = var.s3_force_destroy

  tags = {
    component = "mlflow"
    purpose   = "model-artifacts"
  }
}



module "training_extracts_bucket" {
  source = "../../../modules/s3"

  project_name = var.project_name
  environment  = var.environment

  bucket_name       = local.training_extracts_bucket_name
  enable_versioning = var.enable_versioning

  sse_algorithm = var.s3_sse_algorithm
  force_destroy = var.s3_force_destroy

  tags = {
    component = "ml-training"
    purpose   = "training-extracts"
  }
}



module "forecast_application_bucket" {
  source = "../../../modules/s3"

  project_name = var.project_name
  environment  = var.environment

  bucket_name       = local.forecast_application_bucket_name
  enable_versioning = var.enable_versioning

  sse_algorithm = var.s3_sse_algorithm
  force_destroy = var.s3_force_destroy

  tags = {
    component = "prediction_app"
    purpose   = "forecast_application"
  }
}