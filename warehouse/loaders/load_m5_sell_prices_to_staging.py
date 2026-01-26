"""
warehouse.loaders.load_m5_sell_prices_to_staging

Production-grade staging loader for M5 sell_prices.csv into Redshift using COPY from S3.

- Audit metadata: Postgres (AuditSessionLocal)
- Data load: Redshift via COPY from S3
- Schema lifecycle: dbt (no schema creation here)

Staging is raw: keep values as varchar; dbt Silver will type-cast.
"""

from __future__ import annotations

from sqlalchemy import text

from config.config import settings
from database.database import warehouse_engine, AuditSessionLocal
from ingestion.ingestion_queries import get_latest_successful_ingest_date
from ingestion.bronze_io import build_bronze_key, get_bronze_bucket
from quality.specs.m5_sell_prices import BRONZE_FILENAME

STAGING_TABLE = "m5_sell_prices_raw"


def _recreate_table() -> None:
    # IMPORTANT: column order must match sell_prices.csv exactly
    ddl = f"""
    DROP TABLE IF EXISTS {settings.STAGING_SCHEMA}.{STAGING_TABLE};
    CREATE TABLE {settings.STAGING_SCHEMA}.{STAGING_TABLE} (
        store_id    varchar(32),
        item_id     varchar(64),
        wm_yr_wk    varchar(32),
        sell_price  varchar(32)
    );
    """
    with warehouse_engine.begin() as conn:
        conn.execute(text(ddl))


def _copy_from_s3(s3_path: str) -> None:
    copy_sql = f"""
    COPY {settings.STAGING_SCHEMA}.{STAGING_TABLE}
    FROM '{s3_path}'
    IAM_ROLE '{settings.REDSHIFT_IAM_ROLE_ARN}'
    FORMAT AS CSV
    IGNOREHEADER 1
    EMPTYASNULL
    BLANKSASNULL;
    """
    with warehouse_engine.begin() as conn:
        conn.execute(text(copy_sql))


def load_sell_prices_to_staging() -> None:
    db = AuditSessionLocal()
    try:
        source_name = settings.M5_SOURCE_NAME or "m5_sales"
        bronze_bucket = get_bronze_bucket()

        latest_ingest_date = get_latest_successful_ingest_date(db, source_name=source_name)

        bronze_key = build_bronze_key(
            source_name=source_name,
            ingest_date=latest_ingest_date.isoformat(),
            filename=BRONZE_FILENAME,
        )

        s3_path = f"s3://{bronze_bucket}/{bronze_key}"
        print(f"Loading sell_prices from {s3_path} into Redshift staging")

        _recreate_table()
        _copy_from_s3(s3_path)

        print(f"Loaded {settings.STAGING_SCHEMA}.{STAGING_TABLE} for ingest_date={latest_ingest_date}")
    finally:
        db.close()


if __name__ == "__main__":
    load_sell_prices_to_staging()
