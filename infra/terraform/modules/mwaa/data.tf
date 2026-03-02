# ==============================================================================
# modules/mwaa/data.tf
# ==============================================================================
#
# Purpose
# - Shared AWS data sources used across the MWAA module (primarily IAM policies).
# ==============================================================================

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}
