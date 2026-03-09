"""
warehouse.loaders.load_trends_interest_over_time_to_staging

Purpose
-------
Load raw Trends CSV payloads from Bronze into a Redshift staging table.

Pattern
-------
- Audit metadata: Postgres (AuditSessionLocal)
- Data load: Redshift via COPY from S3
- Schema lifecycle: dbt initializes schemas; this loader owns only the raw
  staging table used by downstream Silver models

Flow
----
1) Find latest SUCCEEDED ingest_date from audit.ingestion_runs
2) Download each raw Trends CSV payload from Bronze
3) Normalize each payload into a single row-based CSV contract
4) Upload the normalized CSV to S3 under a processed/ prefix
5) Recreate staging.trends_interest_over_time_raw
6) COPY the CSV from S3 into Redshift staging
"""

from __future__ import annotations

import csv
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
from sqlalchemy import text

from app_config.config import settings
from database.database import AuditSessionLocal, warehouse_engine
from ingestion.bronze_io import download_bronze_object_to_tempfile, get_bronze_bucket
from ingestion.ingestion_queries import get_latest_successful_ingest_date
from ingestion.s3_client import upload_file_to_bronze
from ingestion.trends.bronze_keys import build_trends_bronze_key
from ingestion.trends.keywords_registry import TRENDS_KEYWORDS
from ingestion.trends.provider_contract import SOURCE_NAME


# ------------------------------------------------------------------------------
# Loader constants
# ------------------------------------------------------------------------------
STAGING_TABLE = "trends_interest_over_time_raw"
PROCESSED_PREFIX = "processed/trends_interest_over_time_raw"


# ------------------------------------------------------------------------------
# Redshift table management
# ------------------------------------------------------------------------------
def _recreate_table() -> None:
    """
    Drop and recreate the raw Trends staging table.
    """
    ddl = f"""
    DROP TABLE IF EXISTS {settings.STAGING_SCHEMA}.{STAGING_TABLE};
    CREATE TABLE {settings.STAGING_SCHEMA}.{STAGING_TABLE} (
        ingest_date      varchar(32)   NOT NULL,
        source_name      varchar(64)   NOT NULL,
        provider         varchar(64)   NOT NULL,
        schema_version   varchar(32)   NOT NULL,
        keyword          varchar(256)  NOT NULL,
        feature_name     varchar(128)  NOT NULL,
        label            varchar(512)  NOT NULL,
        geo              varchar(32)   NOT NULL,
        trend_date       varchar(32)   NOT NULL,
        interest_value   varchar(32)
    );
    """
    with warehouse_engine.begin() as conn:
        conn.execute(text(ddl))


def _copy_from_s3(s3_path: str) -> None:
    """
    COPY the processed CSV from S3 into Redshift staging.
    """
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


# ------------------------------------------------------------------------------
# Payload normalization
# ------------------------------------------------------------------------------
def _write_payload_rows(writer, csv_path: Path, keyword: str) -> int:
    """
    Normalize one raw Trends CSV payload into the staging contract.
    """
    df = pd.read_csv(csv_path)

    interest_columns = [
        c for c in df.columns
        if c not in {
            "date",
            "keyword",
            "feature_name",
            "label",
            "geo",
            "source_name",
            "provider",
            "schema_version",
            "ingest_date",
            "isPartial",
        }
    ]

    if len(interest_columns) != 1:
        raise RuntimeError(
            f"Expected exactly one interest column for keyword={keyword}, "
            f"found={interest_columns}"
        )

    interest_col = interest_columns[0]
    row_count = 0

    for _, row in df.iterrows():
        writer.writerow(
            [
                row["ingest_date"],
                row["source_name"],
                row["provider"],
                row["schema_version"],
                row["keyword"],
                row["feature_name"],
                row["label"],
                row["geo"],
                row["date"],
                row[interest_col],
            ]
        )
        row_count += 1

    return row_count


# ------------------------------------------------------------------------------
# Public loader entrypoint
# ------------------------------------------------------------------------------
def load_trends_interest_over_time_to_staging() -> None:
    """
    Load the latest successfully ingested Trends raw payloads into Redshift staging.
    """
    db = AuditSessionLocal()
    temp_csv_paths: list[Path] = []
    tmp_normalized_csv_path: Path | None = None

    try:
        source_name = settings.TRENDS_SOURCE_NAME or SOURCE_NAME
        bronze_bucket = get_bronze_bucket()

        latest_ingest_date = get_latest_successful_ingest_date(
            db,
            source_name=source_name,
        )

        with NamedTemporaryFile(mode="w", suffix=".csv", newline="", delete=False) as tmp_csv:
            tmp_normalized_csv_path = Path(tmp_csv.name)
            writer = csv.writer(tmp_csv)

            writer.writerow(
                [
                    "ingest_date",
                    "source_name",
                    "provider",
                    "schema_version",
                    "keyword",
                    "feature_name",
                    "label",
                    "geo",
                    "trend_date",
                    "interest_value",
                ]
            )

            total_rows = 0

            for entry in TRENDS_KEYWORDS:
                bronze_key = build_trends_bronze_key(
                    ingest_date=latest_ingest_date.isoformat(),
                    keyword=entry["keyword"],
                )

                csv_path = download_bronze_object_to_tempfile(
                    bucket=bronze_bucket,
                    key=bronze_key,
                )
                temp_csv_paths.append(csv_path)

                row_count = _write_payload_rows(writer, csv_path, entry["keyword"])
                total_rows += row_count

                print(
                    f"Prepared {row_count} Trends rows for "
                    f"{entry['keyword']}"
                )

        processed_key = (
            f"{PROCESSED_PREFIX}/"
            f"source={source_name}/ingest_date={latest_ingest_date.isoformat()}/"
            f"trends_interest_over_time_raw.csv"
        )
        processed_s3_url = upload_file_to_bronze(tmp_normalized_csv_path, processed_key)
        processed_s3_path = f"s3://{bronze_bucket}/{processed_key}"

        print(f"Uploaded processed Trends CSV to {processed_s3_url}")

        _recreate_table()
        _copy_from_s3(processed_s3_path)

        print(
            f"Loaded {settings.STAGING_SCHEMA}.{STAGING_TABLE} "
            f"from ingest_date={latest_ingest_date} "
            f"(rows={total_rows})"
        )

    finally:
        db.close()

        for temp_csv_path in temp_csv_paths:
            try:
                temp_csv_path.unlink(missing_ok=True)
            except Exception:
                pass

        if tmp_normalized_csv_path is not None:
            try:
                tmp_normalized_csv_path.unlink(missing_ok=True)
            except Exception:
                pass


if __name__ == "__main__":
    load_trends_interest_over_time_to_staging()