"""
training.prediction.inference

Utilities for loading the production forecasting model for batch inference.

Purpose
-------
- load the production forecasting model from MLflow Model Registry
- return both the loaded model object and its registered version
- keep model registry access separate from forecast generation logic

Design principles
-----------------
- treat MLflow Model Registry as the source of truth for deployed models
- load the latest registered model version explicitly
- return model metadata needed for forecast writeback and auditing
- avoid deprecated stage-based lookup in production inference
"""

from __future__ import annotations

import mlflow
from mlflow.tracking import MlflowClient

from training.configs.config import get_lightgbm_registered_model_name


# ============================================================
# Model loading
# ============================================================
# Purpose:
# - load the latest registered inference model version
# - expose the model version for warehouse forecast lineage
# - keep MLflow registry access in one reusable place
# ============================================================


def load_latest_model() -> tuple[object, str]:
    """
    Load the latest registered LightGBM model from MLflow.

    Returns
    -------
    tuple[object, str]
        Loaded model object and the MLflow model version string.

    Raises
    ------
    ValueError
        If no registered model versions exist.
    """
    model_name = get_lightgbm_registered_model_name()
    client = MlflowClient()

    latest_versions = client.search_model_versions(f"name = '{model_name}'")

    if not latest_versions:
        raise ValueError(
            f"No registered versions found for model '{model_name}'. "
            "Train and register a model in MLflow first."
        )

    latest_version = max(latest_versions, key=lambda v: int(v.version))
    model_version = str(latest_version.version)

    model_uri = f"models:/{model_name}/{model_version}"
    model = mlflow.lightgbm.load_model(model_uri)

    return model, model_version