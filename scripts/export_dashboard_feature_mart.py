"""
Export the dashboard feature mart to a portable extract.

Usage
-----
PYTHONPATH=. python scripts/export_dashboard_feature_mart.py
"""

from __future__ import annotations

from dashboard.services.export_feature_mart import export_feature_mart_extract


def main() -> None:
    output_path = export_feature_mart_extract()
    print(f"Dashboard feature mart exported to: {output_path}")


if __name__ == "__main__":
    main()