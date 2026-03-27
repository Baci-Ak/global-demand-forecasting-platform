"""
forecast_app.ui.components.cards

Reusable card-style UI helpers for the public forecast application.

Purpose
-------
- keep summary card rendering out of page files
- provide a consistent dashboard look and feel
- support public-facing business summaries
"""

from __future__ import annotations

import streamlit as st

from forecast_app.ui.formatters import format_int, format_timestamp


# ============================================================
# Summary metrics
# ============================================================

def render_summary_metrics(
    *,
    total_forecast: float | int | None,
    average_daily_forecast: float | int | None,
    store_count: int | None,
    product_count: int | None,
) -> None:
    """
    Render the four primary KPI cards for the overview page.
    """
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total forecast demand", format_int(total_forecast))
    col2.metric("Average daily demand", format_int(average_daily_forecast))
    col3.metric("Stores covered", format_int(store_count))
    col4.metric("Products covered", format_int(product_count))


# ============================================================
# Refresh information
# ============================================================

def render_refresh_banner(
    *,
    refreshed_at,
    source_generated_at,
) -> None:
    """
    Render a compact refresh banner in business-friendly language.
    """
    st.caption(
        "Latest published forecast: "
        f"{format_timestamp(source_generated_at)}  •  "
        "App refreshed: "
        f"{format_timestamp(refreshed_at)}"
    )


# ============================================================
# Insight chips
# ============================================================

def render_overview_highlights(highlights: list[str]) -> None:
    """
    Render compact highlight chips for the overview page.
    """
    if not highlights:
        return

    chips_html = "".join(
        f'<span class="gdf-chip">{highlight}</span>'
        for highlight in highlights
    )

    st.markdown(chips_html, unsafe_allow_html=True)