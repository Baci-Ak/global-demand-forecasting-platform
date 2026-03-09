"""
warehouse.loaders.load_macro_series_to_staging

Purpose
-------
Load raw Macro JSON payloads from Bronze into a Redshift staging table.

Pattern
-------
- Audit metadata: Postgres (AuditSessionLocal)
- Data load: Redshift via COPY from S3
- Schema lifecycle: dbt initializes schemas; this loader owns only the raw
  staging table used by downstream Silver models

Flow
----
1) Find latest SUCCEEDED ingest_date from audit.ingestion_runs
2) Download each raw macro JSON payload from Bronze
3) Flatten observations into a row-based CSV
4) Upload the CSV to S3 under a processed/ prefix
5) Recreate staging.macro_series_raw
6) COPY the CSV from S3 into Redshift staging
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from sqlalchemy import text

from app_config.config import settings
from database.database import AuditSessionLocal, warehouse_engine
from ingestion.bronze_io import download_bronze_object_to_tempfile, get_bronze_bucket
from ingestion.ingestion_queries import get_latest_successful_ingest_date
from ingestion.macro.bronze_keys import build_macro_bronze_key
from ingestion.macro.provider_contract import SOURCE_NAME
from ingestion.macro.series_registry import MACRO_SERIES
from ingestion.s3_client import upload_file_to_bronze


# ------------------------------------------------------------------------------
# Loader constants
# ------------------------------------------------------------------------------
STAGING_TABLE = "macro_series_raw"
PROCESSED_PREFIX = "processed/macro_series_raw"


# ------------------------------------------------------------------------------
# Redshift table management
# ------------------------------------------------------------------------------
def _recreate_table() -> None:
    """
    Drop and recreate the raw macro staging table.
    """
    ddl = f"""
    DROP TABLE IF EXISTS {settings.STAGING_SCHEMA}.{STAGING_TABLE};
    CREATE TABLE {settings.STAGING_SCHEMA}.{STAGING_TABLE} (
        ingest_date      varchar(32)   NOT NULL,
        source_name      varchar(64)   NOT NULL,
        provider         varchar(64)   NOT NULL,
        schema_version   varchar(32)   NOT NULL,
        series_id        varchar(64)   NOT NULL,
        feature_name     varchar(128)  NOT NULL,
        series_label     varchar(512)  NOT NULL,
        frequency        varchar(32)   NOT NULL,
        units            varchar(64)   NOT NULL,
        observation_date varchar(32)   NOT NULL,
        observation_value varchar(64)
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
# Payload flattening
# ------------------------------------------------------------------------------
def _write_payload_rows(writer, payload: dict) -> int:
    """
    Write one flattened CSV row per macro observation.
    """
    series_metadata = payload["series_metadata"]
    ingestion_metadata = payload["ingestion_metadata"]
    observations = payload["observations"]

    row_count = 0

    for obs in observations:
        writer.writerow(
            [
                ingestion_metadata["ingest_date"],
                ingestion_metadata["source_name"],
                ingestion_metadata["provider"],
                ingestion_metadata["schema_version"],
                series_metadata["series_id"],
                series_metadata["feature_name"],
                series_metadata["label"],
                series_metadata["frequency"],
                series_metadata["units"],
                obs.get("date"),
                obs.get("value"),
            ]
        )
        row_count += 1

    return row_count


# ------------------------------------------------------------------------------
# Public loader entrypoint
# ------------------------------------------------------------------------------
def load_macro_series_to_staging() -> None:
    """
    Load the latest successfully ingested macro raw payloads into Redshift staging.
    """
    db = AuditSessionLocal()
    temp_json_paths: list[Path] = []
    tmp_csv_path: Path | None = None

    try:
        source_name = settings.MACRO_SOURCE_NAME or SOURCE_NAME
        bronze_bucket = get_bronze_bucket()

        latest_ingest_date = get_latest_successful_ingest_date(
            db,
            source_name=source_name,
        )

        with NamedTemporaryFile(mode="w", suffix=".csv", newline="", delete=False) as tmp_csv:
            tmp_csv_path = Path(tmp_csv.name)
            writer = csv.writer(tmp_csv)

            writer.writerow(
                [
                    "ingest_date",
                    "source_name",
                    "provider",
                    "schema_version",
                    "series_id",
                    "feature_name",
                    "series_label",
                    "frequency",
                    "units",
                    "observation_date",
                    "observation_value",
                ]
            )

            total_rows = 0

            for series in MACRO_SERIES:
                bronze_key = build_macro_bronze_key(
                    ingest_date=latest_ingest_date.isoformat(),
                    series_id=series["series_id"],
                )

                json_path = download_bronze_object_to_tempfile(
                    bucket=bronze_bucket,
                    key=bronze_key,
                )
                temp_json_paths.append(json_path)

                with json_path.open("r", encoding="utf-8") as f:
                    payload = json.load(f)

                row_count = _write_payload_rows(writer, payload)
                total_rows += row_count

                print(
                    f"Prepared {row_count} macro rows for "
                    f"{series['series_id']}"
                )

        processed_key = (
            f"{PROCESSED_PREFIX}/"
            f"source={source_name}/ingest_date={latest_ingest_date.isoformat()}/"
            f"macro_series_raw.csv"
        )
        processed_s3_url = upload_file_to_bronze(tmp_csv_path, processed_key)
        processed_s3_path = f"s3://{bronze_bucket}/{processed_key}"

        print(f"Uploaded processed macro CSV to {processed_s3_url}")

        _recreate_table()
        _copy_from_s3(processed_s3_path)

        print(
            f"Loaded {settings.STAGING_SCHEMA}.{STAGING_TABLE} "
            f"from ingest_date={latest_ingest_date} "
            f"(rows={total_rows})"
        )

    finally:
        db.close()

        for temp_json_path in temp_json_paths:
            try:
                temp_json_path.unlink(missing_ok=True)
            except Exception:
                pass

        if tmp_csv_path is not None:
            try:
                tmp_csv_path.unlink(missing_ok=True)
            except Exception:
                pass


if __name__ == "__main__":
    load_macro_series_to_staging()