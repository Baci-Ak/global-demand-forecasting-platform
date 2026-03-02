project_name = "gdf"
environment = "prod"
aws_region   = "us-east-1"

# Alert recipients (each must confirm subscription email from AWS)
alert_emails = [
  "bassi.cim@gmail.com",
  "akomveronica.a@gmail.com",
]

# -----------------------------
# Cost controls (dev)
# -----------------------------
monthly_budget_usd              = 100
budget_alert_thresholds_percent = [80, 100]

# -----------------------------
# Alarm defaults (dev)
# -----------------------------
alarm_period_seconds      = 300
alarm_evaluation_periods  = 3
alarm_datapoints_to_alarm = 2

# -----------------------------
# RDS Postgres thresholds (dev)
# -----------------------------
# 
rds_cpu_high_threshold               = 80
rds_free_storage_low_threshold_bytes = 10737418240 # 10 GiB
rds_connections_high_threshold       = 200


# -----------------------------
# RDS additional thresholds (dev)
# -----------------------------
rds_freeable_memory_low_threshold_bytes = 268435456 # 256 MiB
rds_disk_queue_depth_high_threshold     = 64


# -----------------------------
# Redshift Serverless thresholds (dev)
# -----------------------------
redshift_rrpu_utilization_high_threshold = 80
redshift_connections_high_threshold      = 200



