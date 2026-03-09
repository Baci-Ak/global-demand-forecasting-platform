"""
Location registry for the Weather source.

Purpose
-------
Keep source geography mapping separate from provider extraction logic.

For the first production-grade integration, we align Weather to the M5 state
geography so downstream joins can be done safely at `state_id`.
"""

from __future__ import annotations


WEATHER_LOCATIONS = [
    {
        "location_id": "CA",
        "state_id": "CA",
        "label": "California",
        "latitude": 36.7783,
        "longitude": -119.4179,
        "timezone": "America/Los_Angeles",
    },
    {
        "location_id": "TX",
        "state_id": "TX",
        "label": "Texas",
        "latitude": 31.9686,
        "longitude": -99.9018,
        "timezone": "America/Chicago",
    },
    {
        "location_id": "WI",
        "state_id": "WI",
        "label": "Wisconsin",
        "latitude": 43.7844,
        "longitude": -88.7879,
        "timezone": "America/Chicago",
    },
]