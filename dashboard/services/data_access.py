"""
Unified dashboard data access layer.

Purpose
-------
Provides a single interface for dashboard pages and components to access data
without knowing whether the backend is:

- warehouse
- extract

This keeps the UI fully decoupled from infrastructure.
"""

from __future__ import annotations

import pandas as pd

from dashboard.core.config import CONFIG
from dashboard.core.constants import SUPPORTED_DATA_BACKENDS
from dashboard.services.extract import (
    read_dq_audit,
    read_feature_mart,
    read_ingestion_audit,
)
from dashboard.services.warehouse import run_query


def _validate_backend() -> str:
    """
    Validate and return the configured backend name.
    """
    backend = CONFIG.data_backend

    if backend not in SUPPORTED_DATA_BACKENDS:
        raise ValueError(
            f"Unsupported DASHBOARD_DATA_BACKEND: {backend}. "
            f"Supported backends: {SUPPORTED_DATA_BACKENDS}"
        )

    return backend


def get_feature_mart_df() -> pd.DataFrame:
    """
    Return the dashboard feature mart from the configured backend.
    """
    backend = _validate_backend()

    if backend == "extract":
        return read_feature_mart()

    sql = "select * from gold.gold_m5_daily_feature_mart"
    return run_query(sql)


def get_ingestion_audit_df() -> pd.DataFrame:
    """
    Return ingestion audit data from the configured backend.
    """
    backend = _validate_backend()

    if backend == "extract":
        return read_ingestion_audit()

    sql = "select * from audit.ingestion_audit_log"
    return run_query(sql)


def get_dq_audit_df() -> pd.DataFrame:
    """
    Return DQ audit data from the configured backend.
    """
    backend = _validate_backend()

    if backend == "extract":
        return read_dq_audit()

    sql = "select * from audit.dq_audit_log"
    return run_query(sql)