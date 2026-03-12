# Dashboard

## Purpose

This folder contains the Streamlit-based forecasting intelligence dashboard for the Global Demand Forecasting project.

The dashboard is designed to support two serving modes:

- **extract**: reads portable Parquet/CSV files from `dashboard/data`
- **warehouse**: reads directly from the analytics warehouse

This keeps the UI decoupled from private infrastructure and allows future deployment to Streamlit Cloud, Hugging Face Spaces, or another platform without forcing direct Redshift access.

## Current structure

- `app.py` — main Streamlit entrypoint
- `pages/` — dashboard pages
- `components/` — reusable UI components
- `services/` — data access and backend logic
- `core/` — config, navigation, constants, and shared state
- `.streamlit/config.toml` — local Streamlit app config
- `data/` — portable extract datasets for non-warehouse deployments

## Runtime configuration

The dashboard uses environment variables for all runtime-sensitive configuration.

### Supported environment variables

- `DASHBOARD_DATA_BACKEND`
  - supported values: `extract`, `warehouse`
  - default: `extract`

- `DASHBOARD_EXTRACT_BASE_PATH`
  - default: `dashboard/data`

- `DASHBOARD_EXTRACT_FORMAT`
  - supported values: `parquet`, `csv`
  - default: `parquet`

- `WAREHOUSE_DSN`
  - required only when `DASHBOARD_DATA_BACKEND=warehouse`

- `DASHBOARD_CACHE_TTL_SECONDS`
  - default: `300`

- `DASHBOARD_ENABLE_EXPORT`
  - default: `true`

- `DASHBOARD_ENABLE_DEBUG_PANELS`
  - default: `false`

## Local run

Install dashboard dependencies:

```bash
pip install -r requirements-dashboard.txt