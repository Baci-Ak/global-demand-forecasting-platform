# ==============================================================================
# envs/dev/ssm-jumphost/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose outputs for downstream stacks (e.g., RDS ingress rules).
# ==============================================================================

output "jumphost_security_group_id" {
  description = "Security group ID for the SSM jump host."
  value       = aws_security_group.jumphost.id
}


output "jumphost_instance_profile_name" {
  description = "Instance profile name for the SSM jump host."
  value       = aws_iam_instance_profile.ssm_jumphost.name
}


output "jumphost_instance_id" {
  description = "EC2 instance ID for the SSM jump host."
  value       = aws_instance.jumphost.id
}


output "iam_terraform_execution_role_arn" {
  description = "IAM stack terraform execution role ARN (from remote state)."
  value       = data.terraform_remote_state.iam.outputs.terraform_execution_role_arn
}
