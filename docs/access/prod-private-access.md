
# Production Environment – Private Access Guide

## Purpose

This document defines the approved method for accessing private infrastructure in the **production environment**.

The following systems are covered:

* Amazon MWAA (Airflow)
* RDS Postgres
* Redshift Serverless

All systems are configured to **deny public internet access**. Access is strictly controlled through AWS IAM and AWS Systems Manager (SSM).

This document is mandatory reading before requesting access.

---

# Security Model

The production environment enforces:

* MWAA `PRIVATE_ONLY`
* RDS in private subnets
* Redshift Serverless in private VPC
* No public ingress rules
* No SSH access
* No bastion SSH keys
* IAM-controlled SSM port forwarding only
* CloudTrail logging enabled
* Budget and CloudWatch alarms configured
* Secrets stored only in AWS Secrets Manager

There is no supported public access path.

---

# Access Requirements

Access to production is restricted.

You must:

1. Be explicitly approved for production access.
2. Be added to the IAM group:

```
gdf-prod-engineers
```

3. Complete security acknowledgement (if required by company policy).

Production access is monitored and logged.

---

# Required Tools

You must have:

### AWS CLI v2

Verify:

```bash
aws --version
```

---

### Session Manager Plugin

Verify:

```bash
session-manager-plugin
```

---

### AWS Authentication

Authenticate using:

* AWS SSO (preferred), or
* IAM credentials issued per policy

Verify correct account:

```bash
aws sts get-caller-identity
```

Confirm you are in the production AWS account before proceeding.

---

# Accessing Production MWAA

MWAA is not publicly reachable.

Access is performed via SSM tunnel.

---

## macOS

Run:

```bash
./gdf-prod-connect-mwaa-mac.sh
```

The script:

* Elevates permissions if required
* Configures local hostname mapping
* Starts SSM tunnel
* Prints the production URL

Keep the terminal open while using Airflow.

---

## Windows / Linux

Run:

```bash
./connect_prod.sh mwaa
```

Open:

```
https://127.0.0.1:8080/
```

Keep the terminal open.

---

# Accessing Production RDS

Start tunnel:

```bash
./connect_prod.sh postgres
```

Connect using:

Host:

```
127.0.0.1
```

Port:

```
5432
```

Credentials are stored in Secrets Manager.

Never store production credentials locally.

---

# Accessing Production Redshift

Start tunnel:

```bash
./connect_prod.sh redshift
```

Connect using:

Host:

```
127.0.0.1
```

Port:

```
5439
```

Use credentials from Secrets Manager.

---

# Monitoring & Logging

All access is logged:

* CloudTrail logs SSM session start/stop
* CloudWatch monitors database health
* Budget alarms notify on cost anomalies
* Redshift usage limits enforce cost caps

Session activity is attributable to IAM identity.

---

# Prohibited Actions

The following are strictly prohibited:

* Opening security groups manually
* Switching MWAA to PUBLIC_ONLY
* Creating direct internet ingress rules
* Sharing production credentials
* Using personal AWS accounts
* Modifying Terraform state manually

All changes must be committed through Terraform.

---

# Incident Response

If unauthorized access is suspected:

1. Terminate active SSM sessions.
2. Review CloudTrail logs.
3. Rotate Secrets Manager credentials if needed.
4. Notify platform owner.

---

# Compliance Statement

Production infrastructure:

* Is private
* Is IAM-controlled
* Is audited
* Is reproducible via Terraform
* Has no public exposure

This document defines the only supported access pattern.
