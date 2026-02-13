# ==============================================================================
# envs/dev/s3/main.tf
# ==============================================================================
#
# Purpose
# - Deploy the dev S3 bucket required for the project.
#
# Notes
# - Bucket names must be globally unique.
# - This stack provisions the bucket and baseline security controls.
#   Access policies are handled separately via IAM.
# ==============================================================================

module "bronze_bucket" {
  source = "../../../modules/s3"

  project_name = var.project_name
  environment  = var.environment

  bucket_name       = "${var.project_name}-${var.environment}-bronze"
  enable_versioning = var.enable_versioning

  sse_algorithm = var.s3_sse_algorithm
  force_destroy = var.s3_force_destroy

  tags = var.s3_bucket_tags
}
