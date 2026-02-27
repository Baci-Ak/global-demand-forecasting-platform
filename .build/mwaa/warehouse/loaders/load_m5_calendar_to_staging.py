"""
warehouse.loaders.load_m5_calendar_to_staging

Production-grade staging loader for M5 calendar.csv into Redshift.

Pattern
-------
- Audit metadata: Postgres (AuditSessionLocal)
- Data load: Redshift via COPY from S3
- Schema lifecycle: dbt (no schema creation here)

Flow
----
1) Find latest SUCCEEDED ingest_date from audit.ingestion_runs (Postgres)
2) Build S3 path for calendar.csv
3) DROP/CREATE staging table in Redshift
4) COPY calendar.csv from S3 into Redshift staging table
"""

from __future__ import annotations

from sqlalchemy import text

from app_config.config import settings
from database.database import warehouse_engine, AuditSessionLocal
from ingestion.ingestion_queries import get_latest_successful_ingest_date
from ingestion.bronze_io import build_bronze_key, get_bronze_bucket
from quality.specs.m5_calendar import BRONZE_FILENAME

STAGING_TABLE = "m5_calendar_raw"


def _recreate_table() -> None:
    # IMPORTANT: column order must match calendar.csv exactly
    ddl = f"""
    DROP TABLE IF EXISTS {settings.STAGING_SCHEMA}.{STAGING_TABLE};
    CREATE TABLE {settings.STAGING_SCHEMA}.{STAGING_TABLE} (
        date          varchar(32),
        wm_yr_wk      varchar(32),
        weekday       varchar(32),
        wday          varchar(32),
        month         varchar(32),
        year          varchar(32),
        d             varchar(32),
        event_name_1  varchar(128),
        event_type_1  varchar(64),
        event_name_2  varchar(128),
        event_type_2  varchar(64),
        snap_CA       varchar(8),
        snap_TX       varchar(8),
        snap_WI       varchar(8)
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
    TIMEFORMAT 'auto'
    DATEFORMAT 'YYYY-MM-DD'
    BLANKSASNULL
    EMPTYASNULL;
    """
    with warehouse_engine.begin() as conn:
        conn.execute(text(copy_sql))


def load_calendar_to_staging() -> None:
    db = AuditSessionLocal()

    try:
        source_name = settings.M5_SOURCE_NAME or "m5_sales"
        bronze_bucket = get_bronze_bucket()

        latest_ingest_date = get_latest_successful_ingest_date(
            db, source_name=source_name
        )

        bronze_key = build_bronze_key(
            source_name=source_name,
            ingest_date=latest_ingest_date.isoformat(),
            filename=BRONZE_FILENAME,
        )

        s3_path = f"s3://{bronze_bucket}/{bronze_key}"

        print(f"Loading calendar from {s3_path} into Redshift staging")

        _recreate_table()
        _copy_from_s3(s3_path)

        print(
            f"Loaded staging.{STAGING_TABLE} from ingest_date={latest_ingest_date}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    load_calendar_to_staging()
