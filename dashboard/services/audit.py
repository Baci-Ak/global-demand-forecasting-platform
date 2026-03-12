"""
Audit service layer.

Purpose
-------
Provides a stable interface for dashboard pages to access operational
observability datasets without caring whether data comes from:

- warehouse
- extract
"""

from __future__ import annotations

import pandas as pd

from dashboard.services.data_access import (
    get_dq_audit_df,
    get_ingestion_audit_df,
)


def load_ingestion_audit() -> pd.DataFrame:
    """
    Return ingestion audit records.
    """
    return get_ingestion_audit_df()


def load_dq_audit() -> pd.DataFrame:
    """
    Return data quality audit records.
    """
    return get_dq_audit_df()