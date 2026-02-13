# ==============================================================================
# envs/dev/iam/main.tf
# ==============================================================================
#
# Purpose
# - Root IAM stack for shared, environment-level IAM resources.
# - This stack owns reusable IAM roles and policies that other stacks can reference.
# ==============================================================================

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "terraform_execution" {
  name = "${var.project_name}-${var.environment}-terraform-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-terraform-exec"
  }
}
