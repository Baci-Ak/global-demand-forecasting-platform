"""
Main Streamlit application entrypoint.

Purpose
-------
Bootstraps the dashboard application, initializes global state,
renders the shared filter bar, and handles sidebar navigation.
"""

from __future__ import annotations

import importlib

import streamlit as st

from dashboard.components.filters import render_filters
from dashboard.core.config import CONFIG
from dashboard.core.navigation import PAGE_REGISTRY
from dashboard.core.state import initialize_state, reset_filters


st.set_page_config(
    page_title=CONFIG.app_name,
    page_icon=CONFIG.app_icon,
    layout=CONFIG.layout,
)

initialize_state()

st.sidebar.title(CONFIG.app_name)

if st.sidebar.button("Reset all filters"):
    reset_filters()

page_labels = [page.label for page in PAGE_REGISTRY]
selected_label = st.sidebar.radio("Navigation", page_labels)
selected_page = next(page for page in PAGE_REGISTRY if page.label == selected_label)

st.title(CONFIG.app_name)
filter_state = render_filters()
st.divider()

module = importlib.import_module(selected_page.module_path)

if hasattr(module, "render"):
    module.render(filter_state)
else:
    st.error(
        f"The page module '{selected_page.module_path}' "
        "does not define a render() function."
    )