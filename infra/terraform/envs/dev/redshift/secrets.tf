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
    username      = var.admin_username
    password      = random_password.redshift_admin.result
    dbname        = var.database_name
    host          = module.redshift.endpoint_address
    port          = module.redshift.endpoint_port
    copy_role_arn = module.redshift.copy_role_arn
  })
}






# ------------------------------------------------------------------------------
# Convenience secret: WAREHOUSE_DSN (what the app expects)
# ------------------------------------------------------------------------------

resource "aws_secretsmanager_secret" "warehouse_dsn" {
  name        = "${var.project_name}/${var.environment}/warehouse_dsn"
  description = "Application DSN for the Redshift warehouse."

  tags = {
    Name = "${var.project_name}-${var.environment}-warehouse-dsn"
  }
}

resource "aws_secretsmanager_secret_version" "warehouse_dsn" {
  secret_id = aws_secretsmanager_secret.warehouse_dsn.id

  # For Redshift Serverless, standard Postgres-style DSN works with psycopg/SQLAlchemy.
  secret_string = format(
    "postgresql://%s:%s@%s:%s/%s",
    var.admin_username,
    random_password.redshift_admin.result,
    module.redshift.endpoint_address,
    module.redshift.endpoint_port,
    var.database_name
  )
}
