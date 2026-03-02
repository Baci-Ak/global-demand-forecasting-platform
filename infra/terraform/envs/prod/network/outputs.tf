# ==============================================================================
# envs/dev/network/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose dev network stack outputs for integration with other stacks.
# ==============================================================================

output "vpc_id" {
  description = "Dev VPC ID."
  value       = module.network.vpc_id
}

output "public_subnet_ids" {
  description = "Dev public subnet IDs."
  value       = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Dev private subnet IDs."
  value       = module.network.private_subnet_ids
}


output "public_route_table_id" {
  description = "Public route table ID."
  value       = module.network.public_route_table_id
}

output "workloads_security_group_id" {
  description = "Shared security group for internal workloads."
  value       = module.network.workloads_security_group_id
}


