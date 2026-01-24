"""
warehouse.loaders.load_m5_calendar_to_staging

Loads the latest successfully ingested M5 calendar.csv (Bronze) into Postgres
staging schema as a table `m5_calendar`.

High-level:
1) Find latest SUCCEEDED ingest_date for source (audit.ingestion_runs)
2) Download bronze object: source=<source_name>/ingest_date=<date>/calendar.csv
3) Read into pandas
4) Write to Postgres staging.<table> (replace)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import text

from config.config import settings
from database.database import engine, SessionLocal
from ingestion.ingestion_queries import get_latest_successful_ingest_date
from ingestion.bronze_io import (
    build_bronze_key,
    download_bronze_object_to_tempfile,
    get_bronze_bucket,
)
from quality.specs.m5_calendar import BRONZE_FILENAME


STAGING_TABLE = "m5_calendar_raw"


def _ensure_schema_exists() -> None:
    schema = settings.STAGING_SCHEMA
    # Ensure schema exists (idempotent)
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema};"))





def load_calendar_to_staging() -> None:
    """
    Main entrypoint: load latest Bronze calendar.csv into staging.m5_calendar_raw.
    """
    
    bronze_bucket = get_bronze_bucket()

    source_name = settings.M5_SOURCE_NAME or "m5_sales"

    db = SessionLocal()
    tmp_path: Path | None = None

    try:
        # Find latest SUCCEEDED partition from audit.ingestion_runs
        latest_ingest_date = get_latest_successful_ingest_date(db, source_name=source_name)
        bronze_key = build_bronze_key(source_name=source_name, ingest_date=latest_ingest_date.isoformat(),filename=BRONZE_FILENAME,)

        print(f"Latest ingest_date for {source_name} = {latest_ingest_date}")
        print(f"Downloading s3://{bronze_bucket}/{bronze_key}")

        # Download file from Bronze
        tmp_path = download_bronze_object_to_tempfile(bucket=bronze_bucket, key=bronze_key)

        # Load into Postgres staging schema
        df = pd.read_csv(tmp_path)

        # Ensure schema exists (idempotent)
        _ensure_schema_exists()

        # Replace-full load for now (simple, deterministic).
        # Later we can do incremental + merge strategy if needed.
        df.to_sql(
            STAGING_TABLE,
            con=engine,
            schema=settings.STAGING_SCHEMA,
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=50_000,
        )

        print(f"Loaded {len(df):,} rows into staging.{STAGING_TABLE} (replace)")

    finally:
        db.close()
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass


if __name__ == "__main__":
    load_calendar_to_staging()








