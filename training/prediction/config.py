"""
training.prediction.config

Configuration for production batch forecasting.

Purpose
-------
- centralize production batch prediction settings
- keep inference settings reproducible and explicit
- prepare forecast outputs for warehouse writeback
- avoid benchmark-only local artifact assumptions

Design principles
-----------------
- keep forecast horizon and history window explicit
- separate model inference settings from persistence settings
- use production-safe schema/table naming for forecast outputs
- allow local artifact writing only as an optional debug convenience
"""

from __future__ import annotations

from dataclasses import dataclass


# ============================================================
# Prediction configuration
# ============================================================
# Purpose:
# - centralize production forecasting settings
# - define the warehouse destination for forecast outputs
# - keep optional local debug artifact output explicit
# ============================================================


@dataclass(frozen=True)
class PredictionConfig:
    """
    Configuration for production batch forecast generation.
    """

    history_days: int = 60
    forecast_horizon: int = 28
    feature_set_name: str = "calendar_lag_rolling_baseline"

    forecast_schema: str = "forecast"
    forecast_table: str = "daily_item_store_forecasts"

    write_local_artifact: bool = False
    output_dir: str = "artifacts/forecasts"
    output_filename: str = "next_28_days_forecast.parquet"