# ==============================================================================
# modules/vpc_endpoints/endpoints.tf
# ==============================================================================
#
# Purpose
# - Create VPC endpoints required by private workloads.
#
# Endpoints
# - S3: Gateway endpoint (route tables)
# - Interface endpoints: logs, sqs, monitoring, kms, secretsmanager, ecr, ssm,
#   airflow control-plane endpoints
# ==============================================================================

locals {
  available_interface_service_names = {
    "logs"           = "com.amazonaws.${var.aws_region}.logs"
    "sqs"            = "com.amazonaws.${var.aws_region}.sqs"
    "monitoring"     = "com.amazonaws.${var.aws_region}.monitoring"
    "kms"            = "com.amazonaws.${var.aws_region}.kms"
    "secretsmanager" = "com.amazonaws.${var.aws_region}.secretsmanager"
    "ecr.api"        = "com.amazonaws.${var.aws_region}.ecr.api"
    "ecr.dkr"        = "com.amazonaws.${var.aws_region}.ecr.dkr"
    "ssm"            = "com.amazonaws.${var.aws_region}.ssm"

    # keep legacy Terraform keys stable for already-created Airflow endpoints
    "airflow_api"    = "com.amazonaws.${var.aws_region}.airflow.api"
    "airflow_env"    = "com.amazonaws.${var.aws_region}.airflow.env"
    "airflow_ops"    = "com.amazonaws.${var.aws_region}.airflow.ops"
  }

  selected_interface_service_names = {
    for name in var.interface_endpoints :
    name => local.available_interface_service_names[name]
  }
}

# ------------------------------------------------------------------------------
# Gateway endpoint: S3
# ------------------------------------------------------------------------------
resource "aws_vpc_endpoint" "s3" {
  count = var.enable_s3_gateway_endpoint ? 1 : 0

  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = var.private_route_table_ids

  tags = merge(
    {
      Name      = "${local.name_prefix}-vpce-s3"
      component = "vpc-endpoints"
    },
    var.tags
  )
}

# ------------------------------------------------------------------------------
# Interface endpoints
# ------------------------------------------------------------------------------
resource "aws_vpc_endpoint" "interface" {
  for_each = local.selected_interface_service_names

  vpc_id              = var.vpc_id
  service_name        = each.value
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.private_subnet_ids
  security_group_ids  = [aws_security_group.vpce.id]
  private_dns_enabled = var.enable_private_dns

  tags = merge(
    {
      Name      = "${local.name_prefix}-vpce-${each.key}"
      component = "vpc-endpoints"
    },
    var.tags
  )
}