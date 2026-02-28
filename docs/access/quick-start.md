# Quick Start – Dev Access

This guide gets you connected in under 5 minutes.

---

## Step 1 – Get Access

Ask to be added to:

```
gdf-dev-engineers
```

---

## Step 2 – Install Required Tools

Install:

* AWS CLI v2
* AWS Session Manager Plugin

---

## Step 3 – Authenticate

If using SSO:

```bash
aws sso login
```

Verify:

```bash
aws sts get-caller-identity
```

---

## Step 4 – Connect

### Airflow (macOS)

```bash
./gdf-dev-connect-mwaa-mac.sh
```

Open the printed URL.

---

### Airflow (Windows/Linux)

```bash
./connect_dev.sh mwaa
```

Open:

```
https://127.0.0.1:8080/
```

---

### Postgres

```bash
./connect_dev.sh postgres
```

Connect to:

```
127.0.0.1:5432
```

---

### Redshift

```bash
./connect_dev.sh redshift
```

Connect to:

```
127.0.0.1:5439
```

---

Keep the tunnel terminal open while connected.

---
