"""
forecast_app.ui.pages.about

About page for the public forecast application.

Purpose
-------
- explain what the application shows
- give users the business context behind the forecast
- describe the data foundation in clear public-facing language
- build trust without exposing internal engineering noise
"""

from __future__ import annotations

import streamlit as st

from forecast_app.ui.styles import render_app_header


def render_about_page(payload: dict) -> None:
    """
    Render the About page.
    """
    render_app_header(
        title="About this forecast",
        subtitle=(
            "Understand what this dashboard shows, how the published forecast window is produced "
            "from the latest available source data, and how to use it as a planning view."
        ),
    )

    st.markdown(
        """
        <div class="gdf-card">
            <div class="gdf-card-title">What this application is for</div>
            <div class="gdf-card-subtitle">
                This dashboard presents published retail demand forecasts across the current forecast window.
                It is designed to help users explore expected demand patterns by date, store, and product
                through an interactive interface.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="gdf-card">
            <div class="gdf-card-title">What the forecast covers</div>
            <div class="gdf-card-subtitle">
                The forecast is built around retail demand at the item and store level. It is intended to support
                planning, operational review, and demand visibility across the published horizon.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="gdf-card">
            <div class="gdf-card-title">Data used in the forecasting workflow</div>
            <div class="gdf-card-subtitle">
                The forecasting workflow is built from a curated warehouse layer that combines core retail demand
                history with supporting context data used during the broader platform workflow.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div class="gdf-card">
                <div class="gdf-card-title">Core retail demand data</div>
                <div class="gdf-card-subtitle">
                    The central forecasting signal comes from the M5 retail demand dataset, which provides
                    item-level and store-level historical sales patterns used to train and evaluate the model.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="gdf-card">
                <div class="gdf-card-title">Supporting context data</div>
                <div class="gdf-card-subtitle">
                    The wider platform also integrates weather, macroeconomic, and search-trend data to support
                    feature experimentation, broader analysis, and future model evolution.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="gdf-card">
            <div class="gdf-card-title">How to use the dashboard</div>
            <div class="gdf-card-subtitle">
                Start with the Overview page for a high-level outlook, then move into Forecast Explorer,
                Store Performance, Product Performance, and Trends to focus on the specific forecast views
                that matter most to you.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="gdf-card">
            <div class="gdf-card-title">How to interpret the forecast</div>
            <div class="gdf-card-subtitle">
                Forecast values should be read as expected demand, not guaranteed results. They are most useful
                for comparing relative demand patterns across products, stores, and dates, and for supporting
                planning decisions with a forward-looking view.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="gdf-card">
            <div class="gdf-card-title">Refresh cycle</div>
            <div class="gdf-card-subtitle">
                The application publishes a 28-day demand forecast generated from the latest available observed
                date in the source retail dataset. Each forecast window starts immediately after the most recent
                source-data date available to the pipeline and extends for the next 28 days. As the source dataset
                is updated with newer retail activity, the forecasting pipeline can publish
                a new forecast window. If the forecast window shown in the application is not
                recent, it reflects the fact that the underlying source dataset has not yet been updated with
                newer observations. The Data & Refresh page shows when the currently published forecast was
                generated and when the application was last refreshed.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )