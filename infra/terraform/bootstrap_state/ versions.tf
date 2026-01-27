/*
  Bootstrap: Remote Terraform State

  Purpose:
  - Create the S3 bucket and DynamoDB table used for Terraform remote state + locking.
  - This stack is applied ONCE per AWS account/region/environment.
*/

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}
