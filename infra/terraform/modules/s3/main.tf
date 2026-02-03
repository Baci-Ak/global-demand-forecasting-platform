# ==============================================================================
# modules/s3/main.tf
# ==============================================================================
#
# Purpose
# - Reusable S3 module for data platform storage buckets.
# - Enforces baseline security and governance controls by default.
#
# Notes
# - This module is environment-agnostic. Environment-specific naming and inputs
#   are provided by the calling root module (envs/*/*).
# ==============================================================================

# ------------------------------------------------------------------------------
# S3 bucket (base)
# ------------------------------------------------------------------------------

resource "aws_s3_bucket" "this" {
  bucket        = var.bucket_name
  force_destroy = var.force_destroy

  tags = var.tags
}

# ------------------------------------------------------------------------------
# Security: block all public access
# ------------------------------------------------------------------------------

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

# ------------------------------------------------------------------------------
# Security: enforce bucket owner ownership (recommended default)
# ------------------------------------------------------------------------------

resource "aws_s3_bucket_ownership_controls" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# ------------------------------------------------------------------------------
# Security: server-side encryption by default (SSE-S3)
# ------------------------------------------------------------------------------

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = var.sse_algorithm
    }
  }
}

# ------------------------------------------------------------------------------
# Data protection: versioning
# ------------------------------------------------------------------------------

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

