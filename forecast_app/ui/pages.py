"""
forecast_app.ui.pages

UI rendering helpers for the Layer 2 Streamlit forecast application.

Purpose
-------
- keep presentation logic separate from the Streamlit entrypoint
- render polished first-release sections for snapshot status, metadata,
  monitoring, and recent forecast rows
- keep the app easy to extend into a fuller multi-page experience later

Design principles
-----------------
- UI should remain thin and readable
- data loading should stay outside rendering helpers
- first release should favor clarity, trust, and polish
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


# ============================================================
# Shared styling
# ============================================================

def render_app_shell_styles() -> None:
    """
    Render lightweight app styling for a cleaner, more polished UI.
    """
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }

        .gdf-section {
            padding: 1rem 1.1rem 1.1rem 1.1rem;
            border: 1px solid rgba(120, 120, 120, 0.15);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.03);
            margin-bottom: 1rem;
        }

        .gdf-section-title {
            font-size: 1.05rem;
            font-weight: 600;
            margin-bottom: 0.35rem;
        }

        .gdf-muted {
            color: rgba(120, 120, 120, 0.95);
            font-size: 0.92rem;
        }

        .gdf-status-ok {
            display: inline-block;
            padding: 0.3rem 0.6rem;
            border-radius: 999px;
            background: rgba(46, 204, 113, 0.12);
            border: 1px solid rgba(46, 204, 113, 0.25);
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 0.4rem;
            margin-bottom: 0.35rem;
        }

        .gdf-status-cache {
            display: inline-block;
            padding: 0.3rem 0.6rem;
            border-radius: 999px;
            background: rgba(241, 196, 15, 0.12);
            border: 1px solid rgba(241, 196, 15, 0.28);
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 0.4rem;
            margin-bottom: 0.35rem;
        }

        .gdf-status-unavailable {
            display: inline-block;
            padding: 0.3rem 0.6rem;
            border-radius: 999px;
            background: rgba(231, 76, 60, 0.12);
            border: 1px solid rgba(231, 76, 60, 0.28);
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 0.4rem;
            margin-bottom: 0.35rem;
        }

        .gdf-divider {
            margin-top: 0.4rem;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Status helpers
# ============================================================

def _source_badge(label: str, source: str) -> str:
    """
    Return a styled source badge.
    """
    if source == "s3_latest":
        badge_class = "gdf-status-ok"
    elif source == "local_cache":
        badge_class = "gdf-status-cache"
    else:
        badge_class = "gdf-status-unavailable"

    return f'<span class="{badge_class}">{label}: {source}</span>'


def render_snapshot_status(
    *,
    metadata_source: str,
    freshness_source: str,
    monitoring_source: str,
    forecast_rows_source: str,
) -> None:
    """
    Render a clean snapshot source status banner.
    """
    badges = "".join(
        [
            _source_badge("Metadata", metadata_source),
            _source_badge("Freshness", freshness_source),
            _source_badge("Monitoring", monitoring_source),
            _source_badge("Forecast rows", forecast_rows_source),
        ]
    )

    st.markdown(
        f"""
        <div class="gdf-section">
            <div class="gdf-section-title">Snapshot Source Status</div>
            <div class="gdf-muted">
                The application prefers the latest successful S3 snapshot and
                automatically falls back to local cached data if S3 is unavailable.
            </div>
            <div class="gdf-divider"></div>
            {badges}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Snapshot summary
# ============================================================

def render_snapshot_metadata(metadata: dict) -> None:
    """
    Render snapshot metadata as clean KPI-style metrics.
    """
    st.markdown(
        """
        <div class="gdf-section">
            <div class="gdf-section-title">Latest Snapshot Summary</div>
            <div class="gdf-muted">
                Current served snapshot metadata for the public-facing forecast application.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    col1.metric("Model Name", str(metadata.get("model_name", "—")))
    col2.metric("Model Version", str(metadata.get("model_version", "—")))
    col3.metric("Feature Set", str(metadata.get("feature_set_name", "—")))

    col4.metric("Forecast Rows", f"{metadata.get('forecast_row_count', '—')}")
    col5.metric("Series Count", f"{metadata.get('forecast_series_count', '—')}")
    col6.metric("Horizon Days", f"{metadata.get('forecast_horizon_days', '—')}")

    st.caption(
        "Snapshot refreshed at: "
        f"{metadata.get('refreshed_at', '—')} | "
        "Forecast generated at: "
        f"{metadata.get('source_generated_at', '—')}"
    )

    st.markdown("---")


# ============================================================
# Data sections
# ============================================================

def render_latest_forecast_freshness(freshness_df: pd.DataFrame) -> None:
    """
    Render the latest forecast freshness section.
    """
    st.markdown(
        """
        <div class="gdf-section">
            <div class="gdf-section-title">Latest Forecast Freshness</div>
            <div class="gdf-muted">
                Most recent forecast batch summary currently being served to users.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if freshness_df.empty:
        st.warning("Latest forecast freshness data is currently unavailable.")
    else:
        st.dataframe(freshness_df, width="stretch")
    st.markdown("---")


def render_forecast_run_monitoring(monitoring_df: pd.DataFrame) -> None:
    """
    Render the forecast run monitoring section.
    """
    st.markdown(
        """
        <div class="gdf-section">
            <div class="gdf-section-title">Forecast Run Monitoring</div>
            <div class="gdf-muted">
                Recent forecast batch history for operational monitoring and review.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if monitoring_df.empty:
        st.warning("Forecast run monitoring data is currently unavailable.")
    else:
        st.dataframe(monitoring_df, width="stretch")
    st.markdown("---")


def render_recent_forecast_rows(forecast_rows_df: pd.DataFrame) -> None:
    """
    Render the recent forecast rows section.
    """
    st.markdown(
        """
        <div class="gdf-section">
            <div class="gdf-section-title">Recent Forecast Rows</div>
            <div class="gdf-muted">
                Latest served forecast rows from the current snapshot dataset.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if forecast_rows_df.empty:
        st.warning("Forecast row data is currently unavailable.")
    else:
        st.dataframe(forecast_rows_df, width="stretch")