# ==============================================================================
# bootstrap/tfstate/s3.tf
# ==============================================================================
#
# Purpose
# - Create the S3 bucket used to store Terraform state files.
#
# Notes
# - Versioning is enabled to allow recovery of prior state versions.
# - Public access is fully blocked as a baseline security control.
# - Default encryption is enabled to protect state at rest.
# ==============================================================================

resource "aws_s3_bucket" "tfstate" {
  bucket = local.state_bucket_name

  tags = {
    name = local.state_bucket_name
  }
}

resource "aws_s3_bucket_ownership_controls" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
