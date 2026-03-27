"""
forecast_app.snapshot_export.config

Configuration for Layer 2 snapshot export.

Purpose
-------
- centralize snapshot export settings
- define S3 snapshot locations and local cache locations
- keep export configuration separate from export logic

Design principles
-----------------
- read configuration from environment variables
- avoid hardcoded credentials
- support both local development and future AWS scheduling
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class SnapshotExportSettings(BaseSettings):
    """
    Runtime settings for Layer 2 snapshot export.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    LAYER2_SNAPSHOT_BUCKET: str | None = None
    LAYER2_SNAPSHOT_PREFIX: str = "layer2"

    LOCAL_SNAPSHOT_CACHE_DIR: str = "forecast_app/local_cache"

    FORECAST_SCHEMA: str = "forecast"
    FORECAST_TABLE: str = "daily_item_store_forecasts"

    FORECAST_RUN_MONITORING_VIEW: str = "staging.gold_ml_forecast_run_monitoring"
    FORECAST_FRESHNESS_VIEW: str = "staging.gold_ml_latest_forecast_freshness"


settings = SnapshotExportSettings()