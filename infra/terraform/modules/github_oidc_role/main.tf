/*
  Module: github_oidc_role
  File: main.tf

  Creates:
  - IAM role trusted by GitHub Actions OIDC provider
  - Minimal IAM policy attachment for Terraform operations (dev)

  Security:
  - Trust is restricted to a single GitHub repo
  - Permissions are intentionally narrow (least privilege)
*/

data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_role" "this" {
  name = var.role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = data.aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:*"
          }
        }
      }
    ]
  })
}

/*
  Minimal policy for Terraform plan/apply on the current GDF resources.

  Scope:
  - S3 (bronze bucket) bucket configuration permissions
  - Budgets (create/read/update/delete)
  - IAM read permissions needed during plan/apply

  Notes:
  - This is intentionally narrow.
  - We will expand permissions later only when we add new AWS resources.
*/

resource "aws_iam_policy" "terraform_minimal" {
  name        = "${var.role_name}-terraform-minimal"
  description = "Least-privilege policy for Terraform operations from GitHub Actions."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3BronzeBucketConfig"
        Effect = "Allow"
        Action = [
          "s3:CreateBucket",
          "s3:DeleteBucket",
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:GetBucketVersioning",
          "s3:PutBucketVersioning",
          "s3:GetBucketPublicAccessBlock",
          "s3:PutBucketPublicAccessBlock",
          "s3:GetEncryptionConfiguration",
          "s3:PutEncryptionConfiguration",
          "s3:GetLifecycleConfiguration",
          "s3:PutLifecycleConfiguration",
          "s3:GetBucketTagging",
          "s3:PutBucketTagging",
          "s3:GetBucketPolicy",
          "s3:PutBucketPolicy",
          "s3:DeleteBucketPolicy"
        ]
        Resource = "*"
      },
      {
        Sid    = "BudgetsManagement"
        Effect = "Allow"
        Action = [
          "budgets:ViewBudget",
          "budgets:ModifyBudget",
          "budgets:CreateBudget",
          "budgets:DeleteBudget",
          "budgets:DescribeBudgets",
          "budgets:DescribeNotificationsForBudget",
          "budgets:CreateNotification",
          "budgets:DeleteNotification",
          "budgets:CreateSubscriber",
          "budgets:DeleteSubscriber"
        ]
        Resource = "*"
      },
      {
        Sid    = "IamReadForTerraform"
        Effect = "Allow"
        Action = [
          "iam:GetRole",
          "iam:ListRolePolicies",
          "iam:ListAttachedRolePolicies",
          "iam:GetPolicy",
          "iam:GetPolicyVersion"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_minimal" {
  role       = aws_iam_role.this.name
  policy_arn = aws_iam_policy.terraform_minimal.arn
}
