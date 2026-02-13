# ==============================================================================
# envs/dev/ssm-jumphost/iam.tf
# ==============================================================================
#
# Purpose
# - IAM role and instance profile for the SSM-managed jump host.
#
# Notes
# - The AmazonSSMManagedInstanceCore managed policy is the standard minimum
#   required for Systems Manager (SSM) to manage the instance.
# - No SSH keys are required when using SSM.
# ==============================================================================

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "ssm_jumphost" {
  name               = "${var.project_name}-${var.environment}-ssm-jumphost-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = {
    Name = "${var.project_name}-${var.environment}-ssm-jumphost-role"
  }
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ssm_jumphost.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ssm_jumphost" {
  name = "${var.project_name}-${var.environment}-ssm-jumphost-profile"
  role = aws_iam_role.ssm_jumphost.name

  tags = {
    Name = "${var.project_name}-${var.environment}-ssm-jumphost-profile"
  }
}
