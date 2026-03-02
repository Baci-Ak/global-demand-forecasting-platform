# ==============================================================================
# modules/network/routes.tf
# ==============================================================================
#
# Purpose
# - Configure routing for public and private subnets.
#
# Routing model
# - Public subnets route 0.0.0.0/0 to the Internet Gateway (IGW).
# - Private subnets route 0.0.0.0/0 to a NAT Gateway for outbound internet access.
#
# NAT strategy
# - single_nat_gateway = true  => one NAT in the first public subnet (dev default)
# - single_nat_gateway = false => one NAT per AZ (higher availability, higher cost)
# ==============================================================================

locals {
  first_az = var.availability_zones[0]
  nat_azs  = var.single_nat_gateway ? [local.first_az] : var.availability_zones
}

# ------------------------------------------------------------------------------
# Public route table: default route to IGW
# ------------------------------------------------------------------------------
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  tags = {
    name = "${var.project_name}-${var.environment}-public-rt"
  }
}

resource "aws_route" "public_default" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

resource "aws_route_table_association" "public" {
  for_each = aws_subnet.public

  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

# ------------------------------------------------------------------------------
# NAT gateways (one or many depending on strategy)
# ------------------------------------------------------------------------------
resource "aws_eip" "nat" {
  for_each = toset(local.nat_azs)

  domain = "vpc"

  tags = {
    name = "${var.project_name}-${var.environment}-nat-eip-${each.value}"
  }
}

resource "aws_nat_gateway" "this" {
  for_each = toset(local.nat_azs)

  allocation_id = aws_eip.nat[each.value].id
  subnet_id     = aws_subnet.public[each.value].id

  tags = {
    name = "${var.project_name}-${var.environment}-nat-${each.value}"
  }

  depends_on = [aws_internet_gateway.this]
}

# ------------------------------------------------------------------------------
# Private route tables: default route to NAT
# ------------------------------------------------------------------------------
resource "aws_route_table" "private" {
  for_each = toset(var.availability_zones)

  vpc_id = aws_vpc.this.id

  tags = {
    name = "${var.project_name}-${var.environment}-private-rt-${each.value}"
  }
}

resource "aws_route" "private_default" {
  for_each = toset(var.availability_zones)

  route_table_id         = aws_route_table.private[each.value].id
  destination_cidr_block = "0.0.0.0/0"

  # If single NAT, all private subnets route via NAT in the first AZ.
  nat_gateway_id = var.single_nat_gateway ? aws_nat_gateway.this[local.first_az].id : aws_nat_gateway.this[each.value].id
}

resource "aws_route_table_association" "private" {
  for_each = aws_subnet.private

  subnet_id      = each.value.id
  route_table_id = aws_route_table.private[each.key].id
}
