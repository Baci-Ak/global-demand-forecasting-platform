"""
training.config

Central configuration helpers for the training package.

Purpose
-------
- Keep training code free from hardcoded environment values
- Provide one clear place to read ML runtime settings
- Avoid loading unrelated application settings in ECS training jobs
- Keep the training package safer for containers, ECS tasks, and tests
"""

from __future__ import annotations

from training.settings import get_training_settings


# ============================================================
# Warehouse configuration
# ============================================================

def get_warehouse_dsn() -> str:
    """
    Return the warehouse DSN used for model training data access.

    Raises
    ------
    ValueError
        If WAREHOUSE_DSN is not configured.
    """
    settings = get_training_settings()

    if not settings.WAREHOUSE_DSN:
        raise ValueError(
            "WAREHOUSE_DSN is not configured. "
            "Set WAREHOUSE_DSN in the environment."
        )

    return settings.WAREHOUSE_DSN


# ============================================================
# MLflow configuration
# ============================================================

def get_mlflow_tracking_uri() -> str:
    """
    Return the MLflow tracking URI.

    Raises
    ------
    ValueError
        If MLFLOW_TRACKING_URI is not configured.
    """
    settings = get_training_settings()

    if not settings.MLFLOW_TRACKING_URI:
        raise ValueError(
            "MLFLOW_TRACKING_URI is not configured. "
            "Set MLFLOW_TRACKING_URI in the environment."
        )

    return settings.MLFLOW_TRACKING_URI


def get_redshift_copy_role_arn() -> str:
    """
    Return the Redshift COPY/UNLOAD IAM role ARN.

    Raises
    ------
    ValueError
        If REDSHIFT_COPY_ROLE_ARN is not configured.
    """
    settings = get_training_settings()

    if not settings.REDSHIFT_COPY_ROLE_ARN:
        raise ValueError(
            "REDSHIFT_COPY_ROLE_ARN is not configured. "
            "Set REDSHIFT_COPY_ROLE_ARN in the environment."
        )

    return settings.REDSHIFT_COPY_ROLE_ARN


def get_mlflow_registered_model_name() -> str:
    """
    Return the registered model name for the Random Forest benchmark.
    """
    return "gdf_random_forest_demand_forecasting"


def get_lightgbm_registered_model_name() -> str:
    """
    Return the registered model name for the LightGBM benchmark.
    """
    return "gdf_lightgbm_demand_forecasting"