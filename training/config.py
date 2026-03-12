"""
training.config

Central configuration helpers for the training package.

Purpose
-------
- Keep training code free from hardcoded environment values
- Provide one clear place to read application settings needed by ML code
- Reuse the project's existing settings model
"""

from app_config.config import settings


def get_warehouse_dsn() -> str:
    """
    Return the warehouse DSN used for model training data access.

    Preference order:
    1) WAREHOUSE_DSN
    2) POSTGRES_DSN

    Raises
    ------
    ValueError
        If neither DSN is configured.
    """
    dsn = settings.WAREHOUSE_DSN or settings.POSTGRES_DSN

    if not dsn:
        raise ValueError(
            "No warehouse DSN configured. Set WAREHOUSE_DSN or POSTGRES_DSN."
        )

    return dsn




def get_mlflow_tracking_uri() -> str:
    """
    Return the MLflow tracking URI.

    This value must be provided through environment configuration.
    """
    if not settings.MLFLOW_TRACKING_URI:
        raise ValueError(
            "MLFLOW_TRACKING_URI is not configured. "
            "Set it in the environment or .env file."
        )

    return settings.MLFLOW_TRACKING_URI



def get_mlflow_registered_model_name() -> str:
    """
    Return the registered model name for the first production candidate.
    """
    return "gdf_random_forest_demand_forecasting"