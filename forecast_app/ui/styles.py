"""
forecast_app.ui.styles

Shared visual styling for the public forecast application.

Purpose
-------
- define the main visual language for the app
- keep app-wide styling out of page files
- support a clean, modern, dashboard-style layout

Design principles
-----------------
- public-facing and business-friendly
- clear visual hierarchy
- minimal noise
- reusable across pages
"""

from __future__ import annotations

import streamlit as st


# ============================================================
# App shell styling
# ============================================================

def apply_global_styles() -> None:
    """
    Apply the shared visual theme for the forecast application.
    """
    st.markdown(
        """
        <style>
        /* -----------------------------------------------------
           Main layout
        ----------------------------------------------------- */
        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 2.2rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 1450px;
        }

        /* -----------------------------------------------------
           Sidebar
        ----------------------------------------------------- */
        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(120, 120, 120, 0.12);
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.2rem;
        }

        /* -----------------------------------------------------
           App title area
        ----------------------------------------------------- */
        .gdf-app-kicker {
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #4f46e5;
            margin-bottom: 0.4rem;
        }

        .gdf-app-title {
            font-size: 2.2rem;
            font-weight: 800;
            line-height: 1.15;
            margin-bottom: 0.4rem;
            color: #111827;
        }

        .gdf-app-subtitle {
            font-size: 1rem;
            color: #6b7280;
            max-width: 900px;
            margin-bottom: 1.2rem;
        }

        /* -----------------------------------------------------
           Card sections
        ----------------------------------------------------- */
        .gdf-card {
            padding: 1.15rem 1.15rem 1rem 1.15rem;
            border: 1px solid rgba(120, 120, 120, 0.12);
            border-radius: 18px;
            background: #ffffff;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
            margin-bottom: 1rem;
        }

        .gdf-card-title {
            font-size: 1.02rem;
            font-weight: 700;
            color: #111827;
            margin-bottom: 0.25rem;
        }

        .gdf-card-subtitle {
            font-size: 0.92rem;
            color: #6b7280;
            margin-bottom: 0.9rem;
        }

        /* -----------------------------------------------------
           Insight chips
        ----------------------------------------------------- */
        .gdf-chip {
            display: inline-block;
            padding: 0.34rem 0.7rem;
            border-radius: 999px;
            font-size: 0.84rem;
            font-weight: 600;
            margin-right: 0.45rem;
            margin-bottom: 0.45rem;
            border: 1px solid rgba(79, 70, 229, 0.16);
            background: rgba(79, 70, 229, 0.08);
            color: #3730a3;
        }

        .gdf-chip-neutral {
            display: inline-block;
            padding: 0.34rem 0.7rem;
            border-radius: 999px;
            font-size: 0.84rem;
            font-weight: 600;
            margin-right: 0.45rem;
            margin-bottom: 0.45rem;
            border: 1px solid rgba(107, 114, 128, 0.18);
            background: rgba(107, 114, 128, 0.08);
            color: #374151;
        }

        /* -----------------------------------------------------
           Sidebar helper text
        ----------------------------------------------------- */
        .gdf-sidebar-title {
            font-size: 1rem;
            font-weight: 800;
            color: #111827;
            margin-bottom: 0.25rem;
        }

        .gdf-sidebar-text {
            font-size: 0.9rem;
            color: #6b7280;
            margin-bottom: 1rem;
            line-height: 1.45;
        }

        /* -----------------------------------------------------
           Hide Streamlit default spacing quirks slightly
        ----------------------------------------------------- */
        div[data-testid="stMetric"] {
            border: 1px solid rgba(120, 120, 120, 0.12);
            border-radius: 16px;
            padding: 0.65rem 0.8rem;
            background: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Shared shell sections
# ============================================================

def render_app_header(*, title: str, subtitle: str) -> None:
    """
    Render the main page header used across the public app.
    """
    st.markdown(
        f"""
        <div class="gdf-app-kicker">Retail Demand Forecasting</div>
        <div class="gdf-app-title">{title}</div>
        <div class="gdf-app-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def render_section_intro(*, title: str, subtitle: str) -> None:
    """
    Render a reusable section container header.
    """
    st.markdown(
        f"""
        <div class="gdf-card">
            <div class="gdf-card-title">{title}</div>
            <div class="gdf-card-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )