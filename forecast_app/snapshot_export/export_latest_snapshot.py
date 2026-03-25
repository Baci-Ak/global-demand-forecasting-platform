"""
forecast_app.snapshot_export.export_latest_snapshot

Entrypoint for exporting Layer 2 app snapshots from the warehouse.

Purpose
-------
- extract app-serving datasets from the warehouse
- write a local last-known-good snapshot cache
- publish versioned and latest snapshots to S3
- publish snapshot metadata for app freshness and fallback handling

Design principles
-----------------
- query once, write many
- keep latest and history paths explicit
- update latest only after a successful export
- preserve local cache for degraded-mode app serving
"""

from __future__ import annotations

from forecast_app.snapshot_export.config import settings
from forecast_app.snapshot_export.queries import (
    fetch_forecast_rows,
    fetch_forecast_run_monitoring,
    fetch_latest_forecast_freshness,
)
from forecast_app.snapshot_export.writer import (
    build_history_prefix,
    build_latest_prefix,
    build_snapshot_run_id,
    upload_dataframe_parquet_to_s3,
    upload_metadata_json_to_s3,
    write_local_metadata,
    write_local_parquet,
)


def build_snapshot_metadata(
    *,
    freshness_df,
    monitoring_df,
    forecast_rows_df,
    run_id: str,
) -> dict:
    """
    Build snapshot metadata for app display and fallback handling.
    """
    latest_row = freshness_df.iloc[0].to_dict() if not freshness_df.empty else {}

    return {
        "snapshot_run_id": run_id,
        "refreshed_at": run_id,
        "source_generated_at": latest_row.get("generated_at"),
        "model_name": latest_row.get("model_name"),
        "model_version": latest_row.get("model_version"),
        "feature_set_name": latest_row.get("feature_set_name"),
        "forecast_row_count": latest_row.get("forecast_row_count", len(forecast_rows_df)),
        "forecast_series_count": latest_row.get("forecast_series_count"),
        "forecast_horizon_days": latest_row.get("forecast_horizon_days"),
        "monitoring_row_count": len(monitoring_df),
    }


def main() -> None:
    """
    Export the latest Layer 2 snapshot datasets.
    """
    run_id = build_snapshot_run_id()
    history_prefix = build_history_prefix(run_id)
    latest_prefix = build_latest_prefix()

    print("Exporting Layer 2 snapshot datasets from warehouse...")

    freshness_df = fetch_latest_forecast_freshness()
    monitoring_df = fetch_forecast_run_monitoring(limit=500)
    forecast_rows_df = fetch_forecast_rows(limit=100000)

    metadata = build_snapshot_metadata(
        freshness_df=freshness_df,
        monitoring_df=monitoring_df,
        forecast_rows_df=forecast_rows_df,
        run_id=run_id,
    )

    # ------------------------------------------------------------------
    # Write local last-known-good cache first
    # ------------------------------------------------------------------
    write_local_parquet(freshness_df, "latest_forecast_freshness.parquet")
    write_local_parquet(monitoring_df, "forecast_run_monitoring.parquet")
    write_local_parquet(forecast_rows_df, "forecast_rows.parquet")
    write_local_metadata(metadata)

    # ------------------------------------------------------------------
    # Publish versioned history snapshot to S3
    # ------------------------------------------------------------------
    upload_dataframe_parquet_to_s3(
        freshness_df,
        bucket=settings.LAYER2_SNAPSHOT_BUCKET,
        key=f"{history_prefix}/latest_forecast_freshness.parquet",
    )
    upload_dataframe_parquet_to_s3(
        monitoring_df,
        bucket=settings.LAYER2_SNAPSHOT_BUCKET,
        key=f"{history_prefix}/forecast_run_monitoring.parquet",
    )
    upload_dataframe_parquet_to_s3(
        forecast_rows_df,
        bucket=settings.LAYER2_SNAPSHOT_BUCKET,
        key=f"{history_prefix}/forecast_rows.parquet",
    )
    upload_metadata_json_to_s3(
        metadata,
        bucket=settings.LAYER2_SNAPSHOT_BUCKET,
        key=f"{history_prefix}/snapshot_metadata.json",
    )

    # ------------------------------------------------------------------
    # Promote latest snapshot in S3 after successful history publish
    # ------------------------------------------------------------------
    upload_dataframe_parquet_to_s3(
        freshness_df,
        bucket=settings.LAYER2_SNAPSHOT_BUCKET,
        key=f"{latest_prefix}/latest_forecast_freshness.parquet",
    )
    upload_dataframe_parquet_to_s3(
        monitoring_df,
        bucket=settings.LAYER2_SNAPSHOT_BUCKET,
        key=f"{latest_prefix}/forecast_run_monitoring.parquet",
    )
    upload_dataframe_parquet_to_s3(
        forecast_rows_df,
        bucket=settings.LAYER2_SNAPSHOT_BUCKET,
        key=f"{latest_prefix}/forecast_rows.parquet",
    )
    upload_metadata_json_to_s3(
        metadata,
        bucket=settings.LAYER2_SNAPSHOT_BUCKET,
        key=f"{latest_prefix}/snapshot_metadata.json",
    )

    print("Layer 2 snapshot export complete.")
    print(f"S3 latest prefix: s3://{settings.LAYER2_SNAPSHOT_BUCKET}/{latest_prefix}")
    print(f"S3 history prefix: s3://{settings.LAYER2_SNAPSHOT_BUCKET}/{history_prefix}")


if __name__ == "__main__":
    main()