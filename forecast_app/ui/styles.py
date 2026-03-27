"""
forecast_app.ui.styles

Shared styling helpers for the public forecast application.

Purpose
-------
- centralize global visual styling
- keep page files focused on content and interaction
- provide a polished, business-friendly interface layer
"""

from __future__ import annotations

import streamlit as st


def apply_global_styles() -> None:
    """
    Apply the global visual styling used across the app.
    """
    st.markdown(
        """
        <style>
        /* ---------------------------------------------------------
           Page shell
        --------------------------------------------------------- */
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(29, 78, 216, 0.06), transparent 28%),
                linear-gradient(180deg, #f8fbff 0%, #f4f7fb 100%);
            color: #0f172a;
        }

        .block-container {
            max-width: 1380px;
            padding-top: 1.4rem;
            padding-bottom: 2rem;
        }

        /* ---------------------------------------------------------
           Sidebar
        --------------------------------------------------------- */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);
            border-right: 1px solid rgba(148, 163, 184, 0.18);
        }

        section[data-testid="stSidebar"] .stRadio > div {
            gap: 0.25rem;
        }

        /* ---------------------------------------------------------
           Header
        --------------------------------------------------------- */
        .gdf-page-header {
            padding: 1.2rem 1.25rem 1rem 1.25rem;
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 22px;
            background: linear-gradient(135deg, #ffffff 0%, #f6faff 100%);
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
            margin-bottom: 1rem;
        }

        .gdf-page-title {
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.15;
            color: #0f172a;
            margin-bottom: 0.35rem;
            letter-spacing: -0.02em;
        }

        .gdf-page-subtitle {
            font-size: 1rem;
            line-height: 1.65;
            color: #475569;
            max-width: 900px;
        }

        /* ---------------------------------------------------------
           Cards
        --------------------------------------------------------- */
        .gdf-card {
            padding: 1.05rem 1.1rem;
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.86);
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
            margin-bottom: 0.95rem;
            backdrop-filter: blur(6px);
        }

        .gdf-card-title {
            font-size: 1.02rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.4rem;
            letter-spacing: -0.01em;
        }

        .gdf-card-subtitle {
            font-size: 0.96rem;
            line-height: 1.68;
            color: #475569;
        }

        /* ---------------------------------------------------------
           Chips
        --------------------------------------------------------- */
        .gdf-chip {
            display: inline-block;
            margin-right: 0.5rem;
            margin-bottom: 0.6rem;
            padding: 0.48rem 0.8rem;
            border-radius: 999px;
            background: rgba(29, 78, 216, 0.08);
            border: 1px solid rgba(29, 78, 216, 0.14);
            color: #1d4ed8;
            font-size: 0.88rem;
            font-weight: 700;
        }

        /* ---------------------------------------------------------
        Sidebar navigation polish
        --------------------------------------------------------- */
        section[data-testid="stSidebar"] label[data-baseweb="radio"] {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 14px;
            padding: 0.35rem 0.55rem;
            margin-bottom: 0.35rem;
            transition: all 0.2s ease;
        }

        section[data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
            background: rgba(255, 255, 255, 0.96);
            border-color: rgba(29, 78, 216, 0.18);
        }

        section[data-testid="stSidebar"] label[data-baseweb="radio"] div[role="radio"] {
            transform: scale(0.92);
        }

        section[data-testid="stSidebar"] label[data-baseweb="radio"] p {
            font-size: 0.96rem;
            font-weight: 600;
            color: #1f2937;
        }


        /* ---------------------------------------------------------
        Filter controls polish
        --------------------------------------------------------- */
        div[data-testid="stDateInput"],
        div[data-testid="stMultiSelect"] {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 16px;
            padding: 0.45rem 0.65rem 0.35rem 0.65rem;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
        }

        div[data-testid="stDateInput"] label,
        div[data-testid="stMultiSelect"] label {
            font-size: 0.92rem;
            font-weight: 700;
            color: #334155;
        }

        div[data-baseweb="select"] > div {
            border: 1px solid rgba(148, 163, 184, 0.18) !important;
            border-radius: 12px !important;
            min-height: 42px !important;
            background: #ffffff !important;
        }

        div[data-baseweb="input"] > div {
            border: 1px solid rgba(148, 163, 184, 0.18) !important;
            border-radius: 12px !important;
            min-height: 42px !important;
            background: #ffffff !important;
        }

        /* ---------------------------------------------------------
           Native Streamlit polish
        --------------------------------------------------------- */
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 18px;
            padding: 0.9rem 1rem;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
        }

        div[data-testid="stMetricLabel"] {
            color: #64748b;
            font-weight: 700;
        }

        div[data-testid="stMetricValue"] {
            color: #0f172a;
            font-weight: 800;
        }

        .stDataFrame, .stTable {
            border-radius: 18px;
            overflow: hidden;
        }

        /* ---------------------------------------------------------
           Small spacing helpers
        --------------------------------------------------------- */
        .gdf-spacer-sm {
            height: 0.35rem;
        }

        .gdf-spacer-md {
            height: 0.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_header(*, title: str, subtitle: str) -> None:
    """
    Render a consistent page header.
    """
    st.markdown(
        f"""
        <div class="gdf-page-header">
            <div class="gdf-page-title">{title}</div>
            <div class="gdf-page-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )