# ==============================================================================
# modules/mwaa/iam_policy_vpc_networking.tf
# ==============================================================================
#
# Purpose
# - Grant MWAA the EC2/VPC permissions it needs to create and manage ENIs in the VPC.
#
# Notes
# - This is intentionally separated from the Airflow/S3/Logs/SQS/KMS policy so
#   "networking permissions" are easy to audit and manage independently.
# ==============================================================================

resource "aws_iam_role_policy" "mwaa_vpc_networking" {
  name = "${local.name_prefix}-vpc-networking"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "VpcNetworking"
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DeleteNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeNetworkInterfacePermissions",
          "ec2:CreateNetworkInterfacePermission",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeSubnets",
          "ec2:DescribeVpcs",
          "ec2:DescribeRouteTables",
          "ec2:DescribeDhcpOptions"
        ]
        Resource = "*"
      }
    ]
  })
}
