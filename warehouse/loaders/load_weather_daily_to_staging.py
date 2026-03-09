"""
warehouse.loaders.load_weather_daily_to_staging

Production-grade staging loader for Weather daily raw JSON payloads into Redshift.

Pattern
-------
- Audit metadata: Postgres (AuditSessionLocal)
- Data load: Redshift via COPY from S3
- Schema lifecycle: dbt owns downstream modeling; this loader owns only the raw
  staging table used by Silver

Flow
----
1) Find latest SUCCEEDED ingest_date from audit.ingestion_runs
2) Download each location's raw JSON payload from Bronze
3) Flatten daily arrays into one row per location_id per weather_date
4) Write a temporary CSV
5) Upload the CSV to S3 under a processed/ prefix
6) Recreate staging.weather_daily_raw
7) COPY the CSV from S3 into Redshift staging
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
from ingestion.s3_client import upload_file_to_bronze
from ingestion.weather.bronze_keys import build_weather_bronze_key
from ingestion.weather.locations import WEATHER_LOCATIONS
from ingestion.weather.provider_contract import SOURCE_NAME


STAGING_TABLE = "weather_daily_raw"
PROCESSED_PREFIX = "processed/weather_daily_raw"


def _recreate_table() -> None:
    ddl = f"""
    DROP TABLE IF EXISTS {settings.STAGING_SCHEMA}.{STAGING_TABLE};
    CREATE TABLE {settings.STAGING_SCHEMA}.{STAGING_TABLE} (
        ingest_date            varchar(32)   NOT NULL,
        source_name            varchar(64)   NOT NULL,
        provider               varchar(64)   NOT NULL,
        schema_version         varchar(32)   NOT NULL,
        location_id            varchar(16)   NOT NULL,
        state_id               varchar(16)   NOT NULL,
        location_label         varchar(128)  NOT NULL,
        location_timezone      varchar(64)   NOT NULL,
        latitude               varchar(32),
        longitude              varchar(32),
        weather_date           varchar(32)   NOT NULL,
        temperature_2m_max     varchar(32),
        temperature_2m_min     varchar(32),
        precipitation_sum      varchar(32),
        wind_speed_10m_max     varchar(32)
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


def _write_payload_rows(writer, payload: dict) -> int:
    daily = payload["daily"]
    location = payload["location"]
    metadata = payload["ingestion_metadata"]

    dates = daily["time"]
    tmax = daily["temperature_2m_max"]
    tmin = daily["temperature_2m_min"]
    precip = daily["precipitation_sum"]
    wind = daily["wind_speed_10m_max"]

    row_count = 0

    for i, weather_date in enumerate(dates):
        writer.writerow(
            [
                metadata["ingest_date"],
                metadata["source_name"],
                metadata["provider"],
                metadata["schema_version"],
                location["location_id"],
                location["state_id"],
                location["label"],
                location["timezone"],
                location["latitude"],
                location["longitude"],
                weather_date,
                tmax[i],
                tmin[i],
                precip[i],
                wind[i],
            ]
        )
        row_count += 1

    return row_count


def load_weather_daily_to_staging() -> None:
    db = AuditSessionLocal()
    temp_json_paths: list[Path] = []
    tmp_csv_path: Path | None = None

    try:
        source_name = settings.WEATHER_SOURCE_NAME or SOURCE_NAME
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
                    "location_id",
                    "state_id",
                    "location_label",
                    "location_timezone",
                    "latitude",
                    "longitude",
                    "weather_date",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "wind_speed_10m_max",
                ]
            )

            total_rows = 0

            for location in WEATHER_LOCATIONS:
                bronze_key = build_weather_bronze_key(
                    ingest_date=latest_ingest_date.isoformat(),
                    location_id=location["location_id"],
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
                    f"Prepared {row_count} weather rows for "
                    f"{location['location_id']}"
                )

        processed_key = (
            f"{PROCESSED_PREFIX}/"
            f"source={source_name}/ingest_date={latest_ingest_date.isoformat()}/"
            f"weather_daily_raw.csv"
        )
        processed_s3_url = upload_file_to_bronze(tmp_csv_path, processed_key)
        processed_s3_path = f"s3://{bronze_bucket}/{processed_key}"

        print(f"Uploaded processed weather CSV to {processed_s3_url}")

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
    load_weather_daily_to_staging()