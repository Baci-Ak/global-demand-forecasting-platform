"""
warehouse.loaders.load_m5_sales_train_validation_to_staging

Production-grade staging loader for M5 sales_train_validation.csv into Redshift.

Why LONG staging (required)
---------------------------
The raw file is extremely wide (~1919 columns). Redshift tables can have at most
1600 columns, so we cannot create a wide staging table.

Correct production approach:
- Stage in LONG format (one row per id per day):
    staging.m5_sales_train_validation_long_raw
      (id, item_id, dept_id, cat_id, store_id, state_id, d, sales)

Loading strategy
----------------
1) Read latest SUCCEEDED ingest_date from Postgres audit
2) Download sales_train_validation.csv from S3 (Bronze)
3) Convert wide -> long (optionally limited days for dev)
4) Write the long dataset to a temp CSV (gzip)
5) Upload that long CSV to S3 (Bronze under a processed/ prefix)
6) Recreate Redshift staging long table
7) COPY the long CSV from S3 into Redshift

Notes
-----
- This keeps the "world-class" pattern: Redshift loads via COPY from S3.
- The "wide -> long" step is a transform job. In future, replace this step with
  Glue/Spark/EMR/Airflow task, but the interface remains identical.
"""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
from sqlalchemy import text

from app_config.config import settings
from database.database import warehouse_engine, AuditSessionLocal
from ingestion.ingestion_queries import get_latest_successful_ingest_date
from ingestion.bronze_io import (
    build_bronze_key,
    download_bronze_object_to_tempfile,
    get_bronze_bucket,
)
from ingestion.s3_client import upload_file_to_bronze
from quality.specs.m5_sales_train_validation import BRONZE_FILENAME


# Target staging table in Redshift (long)
STAGING_TABLE = "m5_sales_train_validation_long_raw"

# Where we store the generated long file in S3
PROCESSED_PREFIX = "processed/m5_sales_train_validation_long"

# Dev-safety:
# - Full history is ~30,490 * 1,913 ≈ 58M rows.
# - Default to last 90 days unless overridden.
MAX_D_COLS = settings.MAX_D_COLS  # set to 1913 for full load


def _recreate_long_table() -> None:
    ddl = f"""
    DROP TABLE IF EXISTS {settings.STAGING_SCHEMA}.{STAGING_TABLE};
    CREATE TABLE {settings.STAGING_SCHEMA}.{STAGING_TABLE} (
        id       varchar(64)  NOT NULL,
        item_id  varchar(64)  NOT NULL,
        dept_id  varchar(64)  NOT NULL,
        cat_id   varchar(64)  NOT NULL,
        store_id varchar(64)  NOT NULL,
        state_id varchar(64)  NOT NULL,
        d        varchar(16)  NOT NULL,
        sales    integer      NOT NULL
    );
    """
    with warehouse_engine.begin() as conn:
        conn.execute(text(ddl))


def _copy_long_from_s3(s3_path: str) -> None:
    copy_sql = f"""
    COPY {settings.STAGING_SCHEMA}.{STAGING_TABLE}
    FROM '{s3_path}'
    IAM_ROLE '{settings.REDSHIFT_IAM_ROLE_ARN}'
    FORMAT AS CSV
    IGNOREHEADER 1
    GZIP
    BLANKSASNULL
    EMPTYASNULL;
    """
    with warehouse_engine.begin() as conn:
        conn.execute(text(copy_sql))


def load_sales_train_validation_to_staging() -> None:
    db = AuditSessionLocal()
    tmp_wide_path: Path | None = None

    try:
        source_name = settings.M5_SOURCE_NAME or "m5_sales"
        bronze_bucket = get_bronze_bucket()

        latest_ingest_date = get_latest_successful_ingest_date(db, source_name=source_name)

        bronze_key = build_bronze_key(
            source_name=source_name,
            ingest_date=latest_ingest_date.isoformat(),
            filename=BRONZE_FILENAME,
        )
        wide_s3_path = f"s3://{bronze_bucket}/{bronze_key}"
        print(f"Loading sales_train_validation from {wide_s3_path} into Redshift staging (LONG)")

        # 1) Download the wide CSV locally (from S3)
        tmp_wide_path = download_bronze_object_to_tempfile(bucket=bronze_bucket, key=bronze_key)

        # 2) Convert wide -> long (chunked to control memory)
        meta_cols = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]

        # Create a gzipped temp file for the long dataset
        with NamedTemporaryFile(suffix=".csv.gz", delete=False) as tmp_long_file:
            tmp_long_path = Path(tmp_long_file.name)

        first = True
        total_rows = 0

        # chunksize chosen to avoid blowing up during melt
        for chunk in pd.read_csv(tmp_wide_path, chunksize=250):
            d_cols_all = [c for c in chunk.columns if c.startswith("d_")]
            if MAX_D_COLS and len(d_cols_all) > MAX_D_COLS:
                d_cols = d_cols_all[-MAX_D_COLS:]
            else:
                d_cols = d_cols_all

            long_df = chunk.melt(
                id_vars=meta_cols,
                value_vars=d_cols,
                var_name="d",
                value_name="sales",
            )

            long_df["sales"] = pd.to_numeric(long_df["sales"], errors="coerce").fillna(0).astype("int64")

            # Append to gzip CSV
            long_df.to_csv(
                tmp_long_path,
                mode="wt" if first else "at",
                index=False,
                header=first,
                compression="gzip",
            )

            total_rows += len(long_df)
            first = False
            print(f"Generated {total_rows:,} long rows so far...")

        # 3) Upload the generated long file back to S3 (Bronze under processed/)
        processed_key = (
            f"{PROCESSED_PREFIX}/"
            f"source={source_name}/ingest_date={latest_ingest_date.isoformat()}/"
            f"sales_train_validation_long.csv.gz"
        )
        processed_s3_url = upload_file_to_bronze(tmp_long_path, processed_key)
        processed_s3_path = f"s3://{bronze_bucket}/{processed_key}"

        print(f"Uploaded LONG file to {processed_s3_url}")

        # 4) Recreate long staging table in Redshift + COPY from S3 (gzip)
        _recreate_long_table()
        _copy_long_from_s3(processed_s3_path)

        print(f"Loaded staging.{STAGING_TABLE} from ingest_date={latest_ingest_date}")

    finally:
        db.close()
        if tmp_wide_path is not None:
            try:
                tmp_wide_path.unlink(missing_ok=True)
            except Exception:
                pass
        # tmp_long_path is defined only if we created it
        try:
            if "tmp_long_path" in locals() and tmp_long_path is not None:
                tmp_long_path.unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == "__main__":
    load_sales_train_validation_to_staging()
