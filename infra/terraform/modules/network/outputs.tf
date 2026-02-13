# ==============================================================================
# modules/network/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose network identifiers for downstream stacks (RDS, MWAA, Redshift).
# ==============================================================================

output "vpc_id" {
  description = "VPC ID."
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs (one per AZ)."
  value       = [for s in aws_subnet.public : s.id]
}

output "private_subnet_ids" {
  description = "List of private subnet IDs (one per AZ)."
  value       = [for s in aws_subnet.private : s.id]
}




output "private_route_table_ids" {
  description = "List of private route table IDs (one per AZ). Used by gateway VPC endpoints (e.g., S3)."
  value       = [for rt in aws_route_table.private : rt.id]
}

output "public_route_table_id" {
  description = "Public route table ID. Usually not needed by downstream stacks."
  value       = aws_route_table.public.id
}

output "workloads_security_group_id" {
  description = "Shared security group id for internal workloads."
  value       = aws_security_group.workloads.id
}
