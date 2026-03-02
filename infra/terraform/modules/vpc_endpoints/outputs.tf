# ==============================================================================
# modules/vpc_endpoints/outputs.tf
# ==============================================================================
#
# Purpose
# - Export endpoint identifiers for visibility/ops.
# ==============================================================================

output "vpce_security_group_id" {
  description = "Security group id attached to interface endpoints."
  value       = aws_security_group.vpce.id
}

output "s3_gateway_endpoint_id" {
  description = "S3 gateway endpoint id (if created)."
  value       = try(aws_vpc_endpoint.s3[0].id, null)
}

output "interface_endpoint_ids" {
  description = "Map of interface endpoint ids by short name."
  value       = { for k, v in aws_vpc_endpoint.interface : k => v.id }
}
