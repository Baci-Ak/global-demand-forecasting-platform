# ==============================================================================
# bootstrap/tfstate/locals.tf
# ==============================================================================
#
# Purpose
# - Define naming conventions for the Terraform remote state backend.
# - Uses a random suffix to ensure global S3 bucket name uniqueness.
# ==============================================================================

resource "random_id" "suffix" {
  byte_length = 3
}

locals {
  state_bucket_name = "${var.project_name}-${var.environment}-tfstate-${random_id.suffix.hex}"
  lock_table_name   = "${var.project_name}-${var.environment}-terraform-locks"
}
