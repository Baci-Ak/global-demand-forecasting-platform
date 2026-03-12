"""
Reusable KPI strip component.

Purpose
-------
Provides a consistent KPI row across dashboard pages.
"""

from __future__ import annotations

import streamlit as st


def render_kpi_strip(kpis: list[dict]) -> None:
    """
    Render a horizontal KPI strip.

    Expected input example:
        [
            {"label": "Total Sales", "value": "1.2M", "delta": "+4.1%"},
            {"label": "Avg Sell Price", "value": "3.42", "delta": None},
        ]
    """
    if not kpis:
        return

    columns = st.columns(len(kpis))

    for column, kpi in zip(columns, kpis):
        with column:
            st.metric(
                label=kpi.get("label", ""),
                value=kpi.get("value", "-"),
                delta=kpi.get("delta"),
            )