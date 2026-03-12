"""
Dashboard query helpers.

Purpose
-------
Defines reusable query text for dashboard-serving datasets.

Important
---------
This module does not execute queries itself. It only centralizes the
warehouse SQL strings used by dashboard services and export jobs.
"""

from __future__ import annotations

from app_config.config import settings
from dashboard.core.constants import GOLD_FEATURE_MART_FQN

INGESTION_RUNS_TABLE = "ingestion_runs"
DQ_RUNS_TABLE = "dq_runs"


def feature_mart_query() -> str:
    """
    Base query for the Gold feature mart.
    """
    return f"""
        select *
        from {GOLD_FEATURE_MART_FQN}
    """


def dashboard_filter_options_query() -> str:
    """
    Small serving query used to populate dashboard slicers without scanning
    the full mart in the app layer.
    """
    return f"""
        select distinct
            state_id,
            store_id,
            cat_id,
            dept_id,
            item_id,
            wm_yr_wk
        from {GOLD_FEATURE_MART_FQN}
        order by
            state_id,
            store_id,
            cat_id,
            dept_id,
            item_id,
            wm_yr_wk
    """


def ingestion_runs_query() -> str:
    """
    Base query for ingestion audit runs.
    """
    return f"""
        select *
        from {settings.AUDIT_SCHEMA}.{INGESTION_RUNS_TABLE}
    """


def dq_runs_query() -> str:
    """
    Base query for DQ audit runs.
    """
    return f"""
        select *
        from {settings.AUDIT_SCHEMA}.{DQ_RUNS_TABLE}
    """