# Dev Environment - Private Access Guide

## Purpose

This document explains how engineers securely access the **dev environment infrastructure** without exposing any services to the public internet.

The following services are accessible:

* Amazon MWAA (Airflow UI)
* RDS Postgres (audit database)
* Redshift Serverless (warehouse)

All access is private and routed through AWS Systems Manager (SSM) using a managed jump host.

No services are publicly exposed.

---

# Architecture Overview

The dev environment is configured with:

* MWAA webserver access mode: `PRIVATE_ONLY`
* RDS Postgres: private subnets only
* Redshift Serverless: private VPC access only
* No inbound internet access rules
* Access via SSM port forwarding through a managed EC2 jump host
* IAM-based access control

Engineers connect using SSM tunnels. Nothing is reachable directly from the public internet.

---

# Access Requirements

Before connecting, you must have:

### 1. IAM Access

You must be added to the IAM group:

```
gdf-dev-engineers
```

This group grants:

* Read access to non-secret SSM parameters under `/gdf/dev/*`
* Permission to start SSM sessions to the dev jump host
* Permission to perform port forwarding via Session Manager

To request access, contact the platform/infra owner.

---

### 2. AWS CLI Installed

Install AWS CLI v2:

[https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)

Verify installation:

```bash
aws --version
```

---

### 3. Session Manager Plugin Installed

Install the AWS Session Manager Plugin:

[https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)

Verify installation:

```bash
session-manager-plugin
```

---

### 4. AWS Credentials Configured

You must authenticate to the correct AWS account.

If using access keys:

```bash
aws configure
```

If using AWS SSO:

```bash
aws sso login
```

Verify identity:

```bash
aws sts get-caller-identity
```

Confirm the correct account ID appears.

---

# Accessing MWAA (Airflow UI)

MWAA is private and not accessible from the public internet.

Access is performed via an SSM tunnel.

---

## macOS Users

Use the provided script:

```
gdf-dev-connect-mwaa-mac.sh
```

Make it executable:

```bash
chmod +x gdf-dev-connect-mwaa-mac.sh
```

Run:

```bash
./gdf-dev-connect-mwaa-mac.sh
```

The script will:

* Elevate permissions if required
* Configure local hostname mapping
* Flush DNS cache
* Start an SSM port-forwarding session
* Print the URL to open

Keep the terminal window open while using Airflow.

Open the printed URL in your browser.

---

## Windows / Linux Users

Use:

```
connect_dev.sh
```

Run:

```bash
./connect_dev.sh mwaa
```

Then open:

```
https://127.0.0.1:8080/
```

Keep the terminal open while using Airflow.

---

# Accessing RDS Postgres

Start tunnel:

```bash
./connect_dev.sh postgres
```

Then connect using your database client:

Host:

```
127.0.0.1
```

Port:

```
5432
```

Use the appropriate database credentials (stored in Secrets Manager, not provided here).

---

# Accessing Redshift Serverless

Start tunnel:

```bash
./connect_dev.sh redshift
```

Then connect via your SQL client:

Host:

```
127.0.0.1
```

Port:

```
5439
```

Use Redshift credentials stored in Secrets Manager.

---

# Security Notes

* No service is publicly accessible.
* All access is authenticated via IAM.
* SSM sessions are logged in CloudTrail.
* Database credentials are stored in AWS Secrets Manager.
* Only non-sensitive connection metadata is stored in Parameter Store.
* Access is restricted to specific EC2 instance IDs.
* Engineers cannot SSH into the jump host.
* No inbound security group rules allow internet traffic.

---

# Troubleshooting

### MWAA does not open

Ensure:

* AWS credentials are valid
* You are logged into the correct AWS account
* The terminal running the tunnel remains open
* You are in the `gdf-dev-engineers` IAM group

Test SSM parameter access:

```bash
aws ssm get-parameters-by-path --path /gdf/dev/
```

If access is denied, your IAM group membership is missing.

---

### Port Already in Use

If port 443 or 8080 is already in use, stop the conflicting service or change the local port via:

```bash
LOCAL_PORT=8443 ./connect_dev.sh mwaa
```

---

# Compliance & Audit Notes

* All access requires IAM authentication.
* All session activity is logged.
* No production credentials are distributed.
* Infrastructure is configured using Terraform.
* No manual security group modifications are permitted.

---

# Responsibility

Access to dev resources is granted for engineering purposes only.

Do not:

* Share credentials
* Bypass IAM controls
* Modify security groups manually
* Attempt direct network access

All changes must go through Terraform.

---

# Future Enhancements

Possible future improvements:

* AWS Client VPN
* Verified Access
* Centralized SSO-based access
* Internal ALB with identity-based authentication

---

# Summary

Dev environment access is:

* Private
* IAM-controlled
* Auditable
* Secure
* Non-public
* Script-based
* Reproducible

This is the only supported access method.

---
