# ==============================================================================
# modules/s3/main.tf
# ==============================================================================
#
# Purpose
# - Provision a single S3 bucket with production-grade defaults:
#   - Block all public access
#   - Enable default server-side encryption
#   - Enable versioning (optional)
#   - Enforce bucket ownership controls
#
# Notes
# - This module intentionally does not define bucket policies.
#   Access should be granted via IAM roles/policies in separate stacks/modules
#   following least privilege.
# ==============================================================================

# ------------------------------------------------------------------------------
# S3 bucket
# ------------------------------------------------------------------------------
resource "aws_s3_bucket" "this" {
  bucket        = var.bucket_name
  force_destroy = var.force_destroy

  tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      component   = "s3"
      name        = var.bucket_name
    },
    var.tags
  )
}

# ------------------------------------------------------------------------------
# Ownership controls (recommended baseline)
# ------------------------------------------------------------------------------
resource "aws_s3_bucket_ownership_controls" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# ------------------------------------------------------------------------------
# Block all public access (defense in depth)
# ------------------------------------------------------------------------------
resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ------------------------------------------------------------------------------
# Default server-side encryption
# ------------------------------------------------------------------------------
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.sse_algorithm
      kms_master_key_id = var.sse_algorithm == "aws:kms" ? var.kms_key_arn : null
    }
  }
}

# ------------------------------------------------------------------------------
# Versioning
# ------------------------------------------------------------------------------
resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}




# ------------------------------------------------------------------------------
# Lifecycle configuration (retention + storage class transitions)
# ------------------------------------------------------------------------------
resource "aws_s3_bucket_lifecycle_configuration" "this" {
  count  = var.enable_lifecycle ? 1 : 0
  bucket = aws_s3_bucket.this.id

  rule {
    id     = "cost-control"
    status = "Enabled"

    filter {
      prefix = ""
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = var.lifecycle_abort_multipart_days
    }

    dynamic "transition" {
      for_each = var.lifecycle_transition_ia_days == null ? [] : [1]
      content {
        days          = var.lifecycle_transition_ia_days
        storage_class = "STANDARD_IA"
      }
    }

    dynamic "transition" {
      for_each = var.lifecycle_transition_glacier_days == null ? [] : [1]
      content {
        days          = var.lifecycle_transition_glacier_days
        storage_class = "GLACIER"
      }
    }

    dynamic "expiration" {
      for_each = var.lifecycle_expire_days == null ? [] : [1]
      content {
        days = var.lifecycle_expire_days
      }
    }

    noncurrent_version_expiration {
      noncurrent_days = var.lifecycle_noncurrent_expire_days
    }
  }
}