# ==============================================================================
# modules/mwaa/locals.tf
# ==============================================================================
#
# Purpose
# - Centralize derived naming used across MWAA module resources.
#
# Notes
# - Keep naming logic in one place so changes do not require editing multiple files.
# ==============================================================================

locals {
  name_prefix = "${var.project_name}-${var.environment}-mwaa"
}
