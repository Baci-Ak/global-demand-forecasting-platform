# ==============================================================================
# modules/network/vpc.tf
# ==============================================================================
#
# Purpose
# - Create the VPC and Internet Gateway (IGW).
#
# Notes
# - The IGW enables outbound/inbound internet connectivity for public subnets.
# - Private subnets do not route directly to the IGW.
# ==============================================================================

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc"
  }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    name = "${var.project_name}-${var.environment}-igw"
  }
}
