
from __future__ import annotations

import pandas as pd
import streamlit as st

def build_forecast_window_label(filtered_df: pd.DataFrame) -> str:
    """
    Build a simple public-facing label for the selected forecast window.
    """
    if filtered_df.empty or "forecast_date" not in filtered_df.columns:
        return "No forecast window available"

    working_df = filtered_df.copy()
    working_df["forecast_date"] = pd.to_datetime(
        working_df["forecast_date"],
        errors="coerce",
    )

    valid_dates = working_df["forecast_date"].dropna()

    if valid_dates.empty:
        return "No forecast window available"

    start_date = valid_dates.min().strftime("%d %b %Y")
    end_date = valid_dates.max().strftime("%d %b %Y")

    return f"Forecast window: {start_date} to {end_date}"