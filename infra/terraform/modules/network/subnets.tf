# ==============================================================================
# modules/network/subnets.tf
# ==============================================================================
#
# Purpose
# - Create public and private subnets across the requested availability zones.
#
# Subnet strategy
# - Public subnets: host NAT gateway(s) and any internet-facing resources (rare).
# - Private subnets: host internal services such as RDS and MWAA.
#
# Notes
# - CIDR allocation is derived deterministically from the VPC CIDR using cidrsubnet.
# ==============================================================================

locals {
  azs = var.availability_zones

  # Create a consistent set of subnet CIDRs across environments.
  # Each AZ gets:
  # - 1 public /20
  # - 1 private /20
  #
  # Example with 2 AZs:
  # public:  10.20.0.0/20,  10.20.16.0/20
  # private: 10.20.32.0/20, 10.20.48.0/20
}

resource "aws_subnet" "public" {
  for_each = toset(local.azs)

  vpc_id                  = aws_vpc.this.id
  availability_zone       = each.value
  map_public_ip_on_launch = true

  cidr_block = cidrsubnet(
    var.vpc_cidr,
    4,
    index(local.azs, each.value)
  )

  tags = {
    name = "${var.project_name}-${var.environment}-public-${each.value}"
    tier = "public"
  }
}

resource "aws_subnet" "private" {
  for_each = toset(local.azs)

  vpc_id            = aws_vpc.this.id
  availability_zone = each.value

  cidr_block = cidrsubnet(
    var.vpc_cidr,
    4,
    index(local.azs, each.value) + 2
  )

  tags = {
    name = "${var.project_name}-${var.environment}-private-${each.value}"
    tier = "private"
  }
}
