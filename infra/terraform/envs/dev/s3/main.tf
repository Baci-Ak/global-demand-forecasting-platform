# ==============================================================================
# envs/dev/s3/main.tf
# ==============================================================================
#
# Purpose
# - Root module for S3 resources in the dev environment.
# - This stack is responsible for data lake storage (bronze) and related buckets.
#
# Design
# - Uses reusable modules defined under infra/terraform/modules.
# - Environment-specific configuration lives here; implementation lives in modules.
# ==============================================================================

locals {
  bronze = {
    name              = "${var.project_name}-${var.environment}-bronze"
    enable_versioning = true
    force_destroy     = var.s3_force_destroy
    sse_algorithm     = var.s3_sse_algorithm
    tags = {
      data_zone = "bronze"
    }
  }

  artifacts = {
    name              = "${var.project_name}-${var.environment}-artifacts"
    enable_versioning = true
    force_destroy     = var.s3_force_destroy
    sse_algorithm     = var.s3_sse_algorithm
    tags = {
      data_zone = "artifacts"
    }
  }
}


module "bronze_bucket" {
  source = "../../../modules/s3"

  bucket_name       = local.bronze.name
  enable_versioning = local.bronze.enable_versioning
  force_destroy     = local.bronze.force_destroy
  sse_algorithm     = local.bronze.sse_algorithm
  tags              = local.bronze.tags
}



module "artifacts_bucket" {
  source = "../../../modules/s3"

  bucket_name       = local.artifacts.name
  enable_versioning = local.artifacts.enable_versioning
  force_destroy     = local.artifacts.force_destroy
  sse_algorithm     = local.artifacts.sse_algorithm
  tags              = local.artifacts.tags
}