# ==============================================================================
# envs/dev/redshift/secrets.tf
# ==============================================================================
#
# Purpose
# - Generate and store Redshift Serverless admin credentials in Secrets Manager.
# ==============================================================================

resource "random_password" "redshift_admin" {
  length           = 24
  special          = true
  override_special = "!@#%^*()-_=+[]{}:,.?"
}

resource "aws_secretsmanager_secret" "redshift_admin" {
  name        = "${var.project_name}/${var.environment}/redshift/admin"
  description = "Admin credentials for Redshift Serverless (${var.project_name}-${var.environment})."

  tags = {
    Name = "${var.project_name}-${var.environment}-redshift-admin-secret"
  }
}

resource "aws_secretsmanager_secret_version" "redshift_admin" {
  secret_id = aws_secretsmanager_secret.redshift_admin.id

  secret_string = jsonencode({
    username = var.admin_username
    password = random_password.redshift_admin.result
    dbname   = var.database_name
    host     = module.redshift.endpoint_address
    port     = module.redshift.endpoint_port
  })
}
