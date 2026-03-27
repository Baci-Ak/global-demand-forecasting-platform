"""
forecast_app.ui.navigation

Sidebar navigation helpers for the public forecast application.

Purpose
-------
- provide one clean place for app navigation
- keep sidebar structure out of the Streamlit entrypoint
- support future growth without cluttering page files
"""

from __future__ import annotations

import streamlit as st


APP_PAGES = [
    "Overview",
    "Forecast Explorer",
    "Store Performance",
    "Product Performance",
    "Trends",
    "Data & Refresh",
    "About",
]


def render_sidebar_navigation() -> str:
    """
    Render the sidebar navigation and return the selected page.
    """
    with st.sidebar:
        st.markdown(
            """
            <div style="margin-bottom: 1.1rem;">
                <div style="
                    font-size: 1.35rem;
                    font-weight: 800;
                    line-height: 1.2;
                    color: #1d4ed8;
                    margin-bottom: 0.35rem;
                ">
                    Global Demand Forecasting
                </div>
                <div style="
                    font-size: 0.94rem;
                    line-height: 1.55;
                    color: #4b5563;
                    padding: 0.85rem 0.95rem;
                    border: 1px solid rgba(59, 130, 246, 0.14);
                    border-radius: 16px;
                    background: rgba(59, 130, 246, 0.05);
                ">
                    Explore forecast outlook, product demand, store performance,
                    and recent forecast updates.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="
                font-size: 0.8rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: #6b7280;
                margin-bottom: 0.35rem;
            ">
                Navigation
            </div>
            """,
            unsafe_allow_html=True,
        )

        selected_page = st.radio(
            "Navigation",
            APP_PAGES,
            index=0,
            label_visibility="collapsed",
        )

    return selected_page