import os
import uuid
from datetime import date, datetime, timezone
from typing import Optional

import psycopg
from dotenv import load_dotenv

load_dotenv()

POSTGRES_DSN = os.getenv("POSTGRES_DSN")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def start_run(source_name: str, ingest_date: date, schema_version: str = "v1") -> uuid.UUID:
    """
    Insert a STARTED row into audit.ingestion_runs and return run_id.
    """
    if not POSTGRES_DSN:
        raise RuntimeError("POSTGRES_DSN is not set. Add it to .env")

    run_id = uuid.uuid4()
    with psycopg.connect(POSTGRES_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit.ingestion_runs
                  (run_id, source_name, ingest_date, status, schema_version, started_at)
                VALUES
                  (%s, %s, %s, 'STARTED', %s, %s)
                """,
                (str(run_id), source_name, ingest_date, schema_version, _utcnow()),
            )
        conn.commit()
    return run_id


def succeed_run(run_id: uuid.UUID, s3_path: str, row_count: Optional[int] = None) -> None:
    """
    Mark a run as SUCCEEDED and record where data landed.
    """
    if not POSTGRES_DSN:
        raise RuntimeError("POSTGRES_DSN is not set. Add it to .env")

    with psycopg.connect(POSTGRES_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE audit.ingestion_runs
                SET status='SUCCEEDED',
                    s3_path=%s,
                    row_count=%s,
                    ended_at=%s,
                    error_message=NULL
                WHERE run_id=%s
                """,
                (s3_path, row_count, _utcnow(), str(run_id)),
            )
        conn.commit()


def fail_run(run_id: uuid.UUID, error_message: str) -> None:
    """
    Mark a run as FAILED and store a short error message.
    """
    if not POSTGRES_DSN:
        raise RuntimeError("POSTGRES_DSN is not set. Add it to .env")

    # keep error_message reasonably sized for DB storage
    msg = (error_message or "")[:5000]

    with psycopg.connect(POSTGRES_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE audit.ingestion_runs
                SET status='FAILED',
                    ended_at=%s,
                    error_message=%s
                WHERE run_id=%s
                """,
                (_utcnow(), msg, str(run_id)),
            )
        conn.commit()
