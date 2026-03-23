# ============================================================
# Training configuration
# ============================================================
# Purpose:
# - centralize training settings for this entrypoint
# - avoid scattering constants across the script
# - make future refactoring to env/config-driven training easier
# ============================================================



from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LightGBMTrainingConfig:
    """
    Configuration for LightGBM training.
    """

    experiment_name: str = "gdf_lightgbm_demand_forecasting"
    feature_set_name: str = "calendar_lag_rolling_baseline"

    limit_series: int | None = None

    horizon_days: int = 28
    n_windows: int = 5

    num_leaves: int = 64
    learning_rate: float = 0.05
    n_estimators: int = 500

    random_state: int = 42






@dataclass(frozen=True)
class RandomForestTrainingConfig:
    """
    Configuration for Random Forest training.
    """

    experiment_name: str = "gdf_random_forest_demand_forecasting"
    feature_set_name: str = "calendar_lag_rolling_baseline"
    limit_series: int | None = None
    horizon_days: int = 28
    n_windows: int = 5
    n_estimators: int = 200
    max_depth: int = 10
    random_state: int = 42
    n_jobs: int = -1