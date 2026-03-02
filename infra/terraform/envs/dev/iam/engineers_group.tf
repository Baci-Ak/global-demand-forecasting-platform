# ==============================================================================
# envs/dev/iam/engineers_group.tf
# ==============================================================================
#
# Purpose
# - Create an IAM Group for engineers and attach the tunnel policy.
# - Engineers added to this group can run connect_dev.sh without repo access.
# ==============================================================================

resource "aws_iam_group" "engineers" {
  name = "${var.project_name}-${var.environment}-engineers"
}

resource "aws_iam_group_policy_attachment" "engineers_tunnels" {
  group      = aws_iam_group.engineers.name
  policy_arn = aws_iam_policy.engineer_tunnels.arn
}

output "engineers_group_name" {
  value       = aws_iam_group.engineers.name
  description = "Add engineers to this IAM group to enable SSM tunnels."
}