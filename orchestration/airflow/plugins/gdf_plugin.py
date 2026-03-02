"""
Airflow plugin surface for the GDF project.


- Operators/Hooks/Sensors/Macros/Timetables

"""

from __future__ import annotations

from airflow.plugins_manager import AirflowPlugin


# Optional: macros can be exposed here later without touching DAG code.
def gdf_hello() -> str:
    return "gdf"


class GDFPlugin(AirflowPlugin):
    name = "gdf_plugin"
    macros = [gdf_hello]