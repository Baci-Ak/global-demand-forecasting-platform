"""
Warehouse service layer.

Purpose
-------
Centralized access to the analytics warehouse used by the dashboard.

This module reuses the project's existing database configuration so the
dashboard does not manage secrets or DSNs separately.
"""

from __future__ import annotations

import pandas as pd
import sqlalchemy as sa
from sqlalchemy import text

from database.database import warehouse_engine


def get_engine() -> sa.Engine:
    """
    Return the shared warehouse engine from the main project.
    """
    return warehouse_engine


def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """
    Execute a SQL query and return a pandas DataFrame.
    """
    engine = get_engine()

    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        rows = result.mappings().all()

    return pd.DataFrame(rows)