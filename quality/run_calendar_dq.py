"""
Bronze DQ gate for M5 calendar.csv (lake-native)

What this script does:
1) Finds the latest SUCCEEDED ingestion partition for source=m5_sales from audit.ingestion_runs
2) Downloads calendar.csv from Bronze (MinIO/S3) for that partition into a temp file
3) Runs basic checks (schema + key constraints + parseability)
4) Logs DQ status to audit.dq_runs (STARTED -> PASSED/FAILED)

Why this matters:
- In production, the lake (S3) is the source of truth, not local staging.
- DQ should always validate the latest successful ingestion automatically.
"""

import os
import uuid
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import boto3
import pandas as pd
import psycopg
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Environment / configuration
# -------------------------------------------------------------------
load_dotenv()

POSTGRES_DSN = os.getenv("POSTGRES_DSN")
if not POSTGRES_DSN:
    raise RuntimeError("POSTGRES_DSN not set in .env")

BRONZE_BUCKET = os.getenv("BRONZE_BUCKET", "demand-forecast-bronze")

# We reuse the same S3-compatible endpoint credentials we already set up for MinIO.
S3_ENDPOINT_URL = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://localhost:9000")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")


# -------------------------------------------------------------------
# Audit logging (dq_runs): insert once, then update on completion
# -------------------------------------------------------------------
def start_dq_run(dq_run_id, dataset_name, suite_name, started_at) -> None:
    """Insert a single dq_run row in STARTED state."""
    with psycopg.connect(POSTGRES_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit.dq_runs
                (dq_run_id, dataset_name, suite_name, status, started_at)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (dq_run_id, dataset_name, suite_name, "STARTED", started_at),
            )
        conn.commit()


def finish_dq_run(dq_run_id, status, ended_at, details_json=None, error_message=None) -> None:
    """Update the dq_run row to PASSED/FAILED and attach details/error."""
    with psycopg.connect(POSTGRES_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE audit.dq_runs
                SET status=%s,
                    ended_at=%s,
                    details_json=%s,
                    error_message=%s
                WHERE dq_run_id=%s
                """,
                (status, ended_at, details_json, error_message, dq_run_id),
            )
        conn.commit()


# -------------------------------------------------------------------
# Latest partition lookup (production-grade: no hardcoded dates)
# -------------------------------------------------------------------
def get_latest_successful_ingest_date(source_name: str) -> str:
    """
    Returns the latest ingest_date (YYYY-MM-DD) for a source_name with status=SUCCEEDED.
    This allows DQ to always validate the most recent successful ingestion automatically.
    """
    with psycopg.connect(POSTGRES_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ingest_date
                FROM audit.ingestion_runs
                WHERE source_name = %s AND status = 'SUCCEEDED'
                ORDER BY ingest_date DESC, ended_at DESC
                LIMIT 1
                """,
                (source_name,),
            )
            row = cur.fetchone()

    if not row:
        raise RuntimeError(f"No SUCCEEDED ingestion_runs found for source_name={source_name}")

    return row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0])


# -------------------------------------------------------------------
# Bronze download helper (MinIO/S3 -> temp file)
# -------------------------------------------------------------------
def download_bronze_object_to_tempfile(bucket: str, key: str) -> Path:
    """
    Downloads s3://bucket/key (MinIO/S3) to a local temporary file and returns the path.
    """
    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    tmp_path = Path(tmp.name)
    tmp.close()

    s3.download_file(bucket, key, str(tmp_path))
    return tmp_path


# -------------------------------------------------------------------
# Actual checks (basic but meaningful)
# -------------------------------------------------------------------
def run_calendar_checks(csv_path: Path) -> dict:
    """
    Minimal, production-sensible checks:
    - required columns exist
    - primary key column 'd' has no nulls and is unique
    - date field parseable
    """
    df = pd.read_csv(csv_path)

    required_cols = {"d", "date", "wm_yr_wk", "weekday"}
    missing = sorted(list(required_cols - set(df.columns)))

    checks = {
        "file": str(csv_path),
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "missing_required_columns": missing,
        "nulls_in_d": int(df["d"].isna().sum()) if "d" in df.columns else None,
        "nulls_in_date": int(df["date"].isna().sum()) if "date" in df.columns else None,
        "d_unique": bool(df["d"].is_unique) if "d" in df.columns else False,
    }

    if "date" in df.columns:
        parsed = pd.to_datetime(df["date"], errors="coerce")
        checks["date_parse_failures"] = int(parsed.isna().sum())
    else:
        checks["date_parse_failures"] = None

    passed = (
        len(missing) == 0
        and checks["nulls_in_d"] == 0
        and checks["nulls_in_date"] == 0
        and checks["d_unique"] is True
        and checks["date_parse_failures"] == 0
    )
    checks["passed"] = bool(passed)
    return checks


# -------------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------------
def main() -> None:
    dataset_name = "m5_calendar"
    suite_name = "calendar_basic_v1"

    source_name = "m5_sales"
    latest_ingest_date = get_latest_successful_ingest_date(source_name)

    bronze_key = f"source={source_name}/ingest_date={latest_ingest_date}/calendar.csv"
    csv_path = None

    dq_run_id = uuid.uuid4()
    started_at = datetime.now(timezone.utc)

    start_dq_run(
        dq_run_id=dq_run_id,
        dataset_name=dataset_name,
        suite_name=suite_name,
        started_at=started_at,
    )

    try:
        # Download the exact object we want to validate from the lake
        csv_path = download_bronze_object_to_tempfile(BRONZE_BUCKET, bronze_key)

        results = run_calendar_checks(csv_path)
        ended_at = datetime.now(timezone.utc)

        if results["passed"]:
            finish_dq_run(
                dq_run_id=dq_run_id,
                status="PASSED",
                ended_at=ended_at,
                details_json=str(results),
            )
            print("DQ PASSED:", results)
        else:
            finish_dq_run(
                dq_run_id=dq_run_id,
                status="FAILED",
                ended_at=ended_at,
                details_json=str(results),
                error_message="Calendar checks failed",
            )
            raise SystemExit(f"DQ FAILED: {results}")

    except Exception as e:
        ended_at = datetime.now(timezone.utc)
        finish_dq_run(
            dq_run_id=dq_run_id,
            status="FAILED",
            ended_at=ended_at,
            error_message=str(e),
        )
        raise

    finally:
        # Always clean temp file if it exists (worker-style ephemeral disk behavior)
        if csv_path:
            try:
                csv_path.unlink(missing_ok=True)
            except Exception:
                pass


if __name__ == "__main__":
    main()
