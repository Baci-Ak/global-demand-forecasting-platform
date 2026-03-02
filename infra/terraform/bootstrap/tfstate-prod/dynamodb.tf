# ==============================================================================
# bootstrap/tfstate/dynamodb.tf
# ==============================================================================
#
# Purpose
# - Create a DynamoDB table used for Terraform state locking.
#
# Notes
# - Terraform uses this table to prevent concurrent operations against the same
#   state backend, reducing the risk of state corruption.
# ==============================================================================

resource "aws_dynamodb_table" "tf_locks" {
  name         = local.lock_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    name = local.lock_table_name
  }
}
