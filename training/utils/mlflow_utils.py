"""
training.mlflow_utils

Helpers for MLflow experiment tracking.

Purpose
-------
- Centralize MLflow setup for training scripts
- Keep training entrypoints clean and free from hardcoded tracking config
"""

from __future__ import annotations

import mlflow

from training.configs.config import get_mlflow_tracking_uri

def configure_mlflow() -> None:
    """
    Configure the MLflow tracking client from application settings.
    """
    mlflow.set_tracking_uri(get_mlflow_tracking_uri())
