"""
warehouse.loaders.load_m5_sell_prices_to_staging

Fast staging loader for M5 sell_prices.csv.

Why this version exists
-----------------------
`pandas.to_sql` issues many INSERTs and becomes slow for multi-million row files.
For production-grade loading into Postgres, use COPY (bulk load).

In AWS/Redshift, the analogous pattern is `COPY` from S3 which is also the
recommended approach.

Flow
----
1) Find latest SUCCEEDED ingest_date for source (audit.ingestion_runs)
2) Download Bronze sell_prices.csv to a temp file
3) Ensure staging schema exists
4) DROP/CREATE staging table (explicit types)
5) COPY CSV into staging table (fast)
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from config.config import settings
from database.database import engine, SessionLocal
from ingestion.ingestion_queries import get_latest_successful_ingest_date
from ingestion.bronze_io import build_bronze_key, download_bronze_object_to_tempfile, get_bronze_bucket
from quality.specs.m5_sell_prices import BRONZE_FILENAME


STAGING_TABLE = "m5_sell_prices_raw"


def _ensure_schema_exists() -> None:
    schema = settings.STAGING_SCHEMA
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema};"))


def _recreate_table() -> None:
    """
    Recreate the staging table with explicit types for fast COPY.
    """
    schema = settings.STAGING_SCHEMA
    ddl = f"""
    DROP TABLE IF EXISTS {schema}.{STAGING_TABLE};
    CREATE TABLE {schema}.{STAGING_TABLE} (
        store_id   text    NOT NULL,
        item_id    text    NOT NULL,
        wm_yr_wk   integer NOT NULL,
        sell_price numeric NOT NULL
    );
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))


def _copy_csv_into_table(csv_path: Path) -> None:
    """
    Use psycopg COPY via SQLAlchemy raw connection.

    This is much faster than INSERT batching.
    """
    schema = settings.STAGING_SCHEMA

    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cur:
            copy_sql = f"""
                COPY {schema}.{STAGING_TABLE} (store_id, item_id, wm_yr_wk, sell_price)
                FROM STDIN WITH (FORMAT csv, HEADER true)
            """
            with open(csv_path, "r", encoding="utf-8") as f:
                cur.copy_expert(copy_sql, f)
        raw_conn.commit()
    finally:
        raw_conn.close()


def load_sell_prices_to_staging() -> None:
    bronze_bucket = get_bronze_bucket()
    source_name = settings.M5_SOURCE_NAME or "m5_sales"

    db = SessionLocal()
    tmp_path: Path | None = None

    try:
        latest_ingest_date = get_latest_successful_ingest_date(db, source_name=source_name)

        bronze_key = build_bronze_key(
            source_name=source_name,
            ingest_date=latest_ingest_date.isoformat(),
            filename=BRONZE_FILENAME,
        )

        print(f"Latest ingest_date for {source_name} = {latest_ingest_date}")
        print(f"Downloading s3://{bronze_bucket}/{bronze_key}")

        tmp_path = download_bronze_object_to_tempfile(bucket=bronze_bucket, key=bronze_key)

        _ensure_schema_exists()
        _recreate_table()

        print(f"Bulk loading into {settings.STAGING_SCHEMA}.{STAGING_TABLE} via COPY...")
        _copy_csv_into_table(tmp_path)
        print(f"Loaded {settings.STAGING_SCHEMA}.{STAGING_TABLE} successfully.")

    finally:
        db.close()
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass


if __name__ == "__main__":
    load_sell_prices_to_staging()
