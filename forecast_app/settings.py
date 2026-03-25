"""
forecast_app.settings

Shared configuration for the Layer 2 forecast application.

Purpose
-------
- centralize app runtime settings
- keep warehouse and snapshot configuration outside UI code
- support both local development and future deployed execution

Design principles
-----------------
- read configuration from environment variables
- avoid hardcoded credentials
- support direct warehouse reads for local development
- support snapshot-based serving for deployed production
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class ForecastAppSettings(BaseSettings):
    """
    Runtime settings for the forecast application.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    REDSHIFT_HOST: str
    REDSHIFT_USER: str
    REDSHIFT_PASSWORD: str
    REDSHIFT_PORT: int = 5439
    REDSHIFT_DBNAME: str = "warehouse"

    FORECAST_SCHEMA: str = "forecast"
    FORECAST_TABLE: str = "daily_item_store_forecasts"

    FORECAST_RUN_MONITORING_VIEW: str = "staging.gold_ml_forecast_run_monitoring"
    FORECAST_FRESHNESS_VIEW: str = "staging.gold_ml_latest_forecast_freshness"


settings = ForecastAppSettings()