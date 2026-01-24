"""
warehouse.loaders.load_m5_sales_train_validation_to_staging

Staging loader for M5 sales_train_validation.csv into Postgres.

Key constraint (local dev)
--------------------------
`sales_train_validation.csv` is extremely wide (1919 columns, 1913 of them d_*).
Postgres tables have a hard limit of 1600 columns, so we cannot load the raw wide
file into a single staging table.

Instead, we load the dataset into a LONG staging table:

    staging.m5_sales_train_validation_long_raw
      (id, item_id, dept_id, cat_id, store_id, state_id, d, sales)

This is also the shape we ultimately want for modeling and joins.

Production note (Redshift)
--------------------------
In Redshift we COPY wide, but it's still more useful downstream to work in
long format. typically:
- COPY the raw file into a staging table (either wide or semi-structured),
- then transform to long in dbt.
Locally we skip the wide step because Postgres can't support it.

Flow
----
1) Find latest SUCCEEDED ingest_date for source (audit.ingestion_runs)
2) Download Bronze sales_train_validation.csv to a temp file
3) Ensure staging schema exists
4) DROP/CREATE long staging table
5) Read CSV in chunks, melt d_* columns into long rows, append to staging table
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
from quality.specs.m5_sales_train_validation import BRONZE_FILENAME


STAGING_TABLE = "m5_sales_train_validation_long_raw"

# Local-dev safety: the long form explodes to ~58M rows if we melt all days.
# Default to last 90 days. In production we can set this to 1913 (full history).
MAX_D_COLS = 90



def _ensure_schema_exists() -> None:
    schema = settings.STAGING_SCHEMA
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema};"))


def _recreate_table() -> None:
    """
    Recreate LONG staging table (one row per series per day).

    This avoids Postgres' 1600-column limit.
    """
    schema = settings.STAGING_SCHEMA
    ddl = f"""
    DROP TABLE IF EXISTS {schema}.{STAGING_TABLE};
    CREATE TABLE {schema}.{STAGING_TABLE} (
        id text NOT NULL,
        item_id text NOT NULL,
        dept_id text NOT NULL,
        cat_id text NOT NULL,
        store_id text NOT NULL,
        state_id text NOT NULL,
        d text NOT NULL,
        sales integer NOT NULL
    );
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))


def load_sales_train_validation_to_staging() -> None:
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

        print(f"Loading into {settings.STAGING_SCHEMA}.{STAGING_TABLE} (wide -> long, chunked)...")

        meta_cols = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
        first = True
        total_rows = 0

        # NOTE: chunksize is intentionally small because each chunk expands ~1913x during melt.
        for chunk in pd.read_csv(tmp_path, chunksize=250):
            d_cols_all = [c for c in chunk.columns if c.startswith("d_")]
            d_cols = d_cols_all[-MAX_D_COLS:] if MAX_D_COLS and len(d_cols_all) > MAX_D_COLS else d_cols_all


            long_df = chunk.melt(
                id_vars=meta_cols,
                value_vars=d_cols,
                var_name="d",
                value_name="sales",
            )

            # hygiene: ensure integer sales, defaulting nulls to 0
            long_df["sales"] = pd.to_numeric(long_df["sales"], errors="coerce").fillna(0).astype("int64")

            long_df.to_sql(
                STAGING_TABLE,
                con=engine,
                schema=settings.STAGING_SCHEMA,
                if_exists="replace" if first else "append",
                index=False,
                method="multi",
                chunksize=50_000,
            )

            total_rows += len(long_df)
            first = False
            print(f"Loaded {total_rows:,} rows so far into {settings.STAGING_SCHEMA}.{STAGING_TABLE}")

        print(f"Loaded {total_rows:,} rows into {settings.STAGING_SCHEMA}.{STAGING_TABLE}")

    finally:
        db.close()
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass


if __name__ == "__main__":
    load_sales_train_validation_to_staging()
