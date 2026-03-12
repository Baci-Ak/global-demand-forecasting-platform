"""
Extract data access service.

Purpose
-------
Provides a portable, non-warehouse data source for the dashboard.

This lets the dashboard run without direct access to Redshift or any
private AWS network path. It reads pre-exported datasets from local files,
which is ideal for Streamlit Cloud, Hugging Face Spaces, demos, and
decoupled deployments.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from dashboard.core.config import CONFIG
from dashboard.core.constants import (
    DQ_AUDIT_DATASET,
    FEATURE_MART_DATASET,
    INGESTION_AUDIT_DATASET,
)


def _dataset_path(dataset_name: str) -> Path:
    """
    Resolve the full path for a dataset based on configured extract format.
    """
    base_path = Path(CONFIG.extract_base_path)
    suffix = ".parquet" if CONFIG.extract_format == "parquet" else ".csv"
    return base_path / f"{dataset_name}{suffix}"


def read_dataset(dataset_name: str) -> pd.DataFrame:
    """
    Read a configured extract dataset into a pandas DataFrame.
    """
    path = _dataset_path(dataset_name)

    if not path.exists():
        raise FileNotFoundError(
            f"Extract dataset not found: {path}. "
            "Ensure the extract files have been generated and placed in the "
            "configured extract base path."
        )

    if CONFIG.extract_format == "parquet":
        return pd.read_parquet(path)

    if CONFIG.extract_format == "csv":
        return pd.read_csv(path)

    raise ValueError(
        f"Unsupported extract format: {CONFIG.extract_format}. "
        "Supported formats are 'parquet' and 'csv'."
    )


def read_feature_mart() -> pd.DataFrame:
    """Read the feature mart extract."""
    return read_dataset(FEATURE_MART_DATASET)


def read_ingestion_audit() -> pd.DataFrame:
    """Read the ingestion audit extract."""
    return read_dataset(INGESTION_AUDIT_DATASET)


def read_dq_audit() -> pd.DataFrame:
    """Read the DQ audit extract."""
    return read_dataset(DQ_AUDIT_DATASET)