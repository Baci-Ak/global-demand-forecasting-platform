# Platform Admin – Access Provisioning Checklist

This checklist must be completed when onboarding a new engineer.

---

## 1. IAM Access

* [ ] Confirm engineer identity
* [ ] Add user to IAM group:

  * `gdf-dev-engineers`
  * `gdf-prod-engineers` (if approved)
* [ ] Verify group membership

---

## 2. AWS Account Confirmation

* [ ] Confirm correct AWS account ID
* [ ] Confirm environment separation (dev vs prod)

---

## 3. Tool Verification

Engineer confirms:

* [ ] AWS CLI installed
* [ ] Session Manager Plugin installed
* [ ] AWS authentication successful
* [ ] `aws sts get-caller-identity` returns correct account

---

## 4. Parameter Store Verification

Test:

```bash
aws ssm get-parameters-by-path --path /gdf/dev/
```

Confirm no permission errors.

---

## 5. Access Test

Engineer runs:

```bash
./connect_dev.sh mwaa
```

Confirm:

* [ ] Tunnel starts
* [ ] Airflow UI loads
* [ ] Postgres connection works
* [ ] Redshift connection works

---

## 6. Audit Confirmation

* [ ] Verify SSM session visible in CloudTrail
* [ ] Verify no public exposure exists
* [ ] Confirm no manual SG changes

---

## 7. Documentation Shared

* [ ] Share Dev Private Access Guide
* [ ] Share Quick Start Guide

---

## 8. Offboarding Procedure (For Future)

When removing engineer:

* [ ] Remove from IAM groups
* [ ] Invalidate SSO session
* [ ] Rotate credentials if required


