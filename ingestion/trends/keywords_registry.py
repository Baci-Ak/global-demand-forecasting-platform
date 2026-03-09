"""
Keyword registry for the Trends source.

Purpose
-------
Keep the list of search-intent keywords separate from extraction logic so the
platform can scale cleanly as we add or refine demand-intent signals.

Design
------
- One registry entry per keyword/topic we want to track.
- `keyword` is the provider query term.
- `feature_name` is the stable internal name we will use downstream.
- Start with a small, high-signal set aligned to retail demand context.
"""

from __future__ import annotations


TRENDS_KEYWORDS = [
    {
        "keyword": "walmart",
        "feature_name": "trends_walmart",
        "label": "Search interest for Walmart",
        "geo": "US",
    },
    {
        "keyword": "grocery store",
        "feature_name": "trends_grocery_store",
        "label": "Search interest for grocery store",
        "geo": "US",
    },
    {
        "keyword": "discount store",
        "feature_name": "trends_discount_store",
        "label": "Search interest for discount store",
        "geo": "US",
    },
    {
        "keyword": "cleaning supplies",
        "feature_name": "trends_cleaning_supplies",
        "label": "Search interest for cleaning supplies",
        "geo": "US",
    },
]