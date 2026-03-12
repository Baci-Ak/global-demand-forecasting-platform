"""
Feature mart export utility.

Purpose
-------
Exports the dashboard-serving feature mart to a portable extract file so
the Streamlit app can run without direct warehouse connectivity.

Important
---------
This exporter always reads from the warehouse source directly.
It must not depend on the dashboard's configured runtime backend.
"""

from __future__ import annotations

from pathlib import Path

from dashboard.core.config import CONFIG
from dashboard.core.constants import FEATURE_MART_DATASET
from dashboard.services.queries import feature_mart_query
from dashboard.services.warehouse import run_query


def export_feature_mart_extract() -> Path:
    """
    Export the feature mart to the configured extract location.
    """
    df = run_query(feature_mart_query())

    output_dir = Path(CONFIG.extract_base_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    if CONFIG.extract_format == "parquet":
        output_path = output_dir / f"{FEATURE_MART_DATASET}.parquet"
        df.to_parquet(output_path, index=False)
        return output_path

    if CONFIG.extract_format == "csv":
        output_path = output_dir / f"{FEATURE_MART_DATASET}.csv"
        df.to_csv(output_path, index=False)
        return output_path

    raise ValueError(
        f"Unsupported extract format: {CONFIG.extract_format}. "
        "Supported formats are 'parquet' and 'csv'."
    )


if __name__ == "__main__":
    path = export_feature_mart_extract()
    print(f"Exported feature mart extract to: {path}")