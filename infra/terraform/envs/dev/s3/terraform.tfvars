# ==============================================================================
# envs/dev/s3/terraform.tfvars
# ==============================================================================
#
# Purpose
# - Environment inputs for the dev S3 stack.
# - Values here should be safe to commit (no secrets).
# ==============================================================================

# ------------------------------------------------------------------------------
# Global environment identity
# ------------------------------------------------------------------------------

# Project identifier used for naming and tagging.
project_name = "gdf"

# Deployment environment label (dev/prod).
environment = "dev"

# AWS region to deploy into.
aws_region = "us-east-1"

# ------------------------------------------------------------------------------
# S3 defaults (dev)
# ------------------------------------------------------------------------------

# Enable versioning for the bronze bucket.
enable_versioning = true

# Extra tags applied to the bronze bucket (in addition to provider default_tags).
s3_bucket_tags = {
  data_zone = "bronze"
  dataset   = "m5"
}

# Bucket encryption algorithm:
# - "AES256"  => SSE-S3 (AWS-managed keys)
# - "aws:kms" => SSE-KMS (customer-managed key)
s3_sse_algorithm = "AES256"

# Allow Terraform to delete objects when destroying dev buckets.
# WARNING: If true, `terraform destroy` can permanently delete bucket contents.
s3_force_destroy = true





# ------------------------------------------------------------------------------
# Bronze lifecycle retention (dev)
# ------------------------------------------------------------------------------

# The bronze bucket stores raw ingested data.
# These settings control storage cost optimization and automatic cleanup.
# Adjust values per environment (dev/prod) as needed.

# Enable lifecycle management on the bronze bucket.
# If false, objects will never transition or expire automatically.
bronze_enable_lifecycle = true

# Abort incomplete multipart uploads after N days.
# Prevents storage waste from failed/abandoned uploads.
bronze_lifecycle_abort_multipart_days = 7


bronze_lifecycle_transition_ia_days      = 30
bronze_lifecycle_transition_glacier_days = 90

# Permanently delete (expire) current objects after N days.
# This enforces data retention policy and controls storage cost.
# Set to null if bronze should be retained indefinitely.
bronze_lifecycle_expire_days = 180


# Delete noncurrent (older versioned) objects after N days.
# Since versioning is enabled, old versions accumulate cost.
# This prevents version sprawl and keeps storage controlled.
bronze_lifecycle_noncurrent_expire_days = 30