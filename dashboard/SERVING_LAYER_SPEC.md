# Dashboard Serving Layer Spec

## Purpose

Define the dashboard-serving datasets so the Streamlit app is decoupled from direct warehouse access and does not depend on exporting a raw full mart blindly.

The source mart is:

- `gold.gold_m5_daily_feature_mart`

Current source shape observed:

- 2,744,100 rows
- 30,490 distinct `id` series
- 3,049 distinct items
- 10 stores
- 3 states
- 90 dates (`2016-01-26` to `2016-04-24`)

## Serving design principle

The dashboard should consume **purpose-built serving extracts**, not a single uncontrolled raw dump.

## v1 serving datasets

### 1. `dashboard_filter_options`
Purpose:
- populate slicers quickly without scanning the full mart

Fields:
- `state_id`
- `store_id`
- `cat_id`
- `dept_id`
- `item_id`
- `wm_yr_wk`

Notes:
- can be materialized from distinct values
- very small dataset

---

### 2. `dashboard_exec_daily`
Purpose:
- support Executive Overview
- support Sales & Demand top-level trend visuals
- support lightweight KPI calculations

Grain:
- `date x state_id x cat_id x dept_id`

Measures:
- `sales`
- `avg_sell_price`
- `avg_temperature_2m_max`
- `avg_temperature_2m_min`
- `sum_precipitation_sum`
- `avg_wind_speed_10m_max`
- `avg_cpi_all_items`
- `avg_unemployment_rate`
- `avg_federal_funds_rate`
- `avg_nonfarm_payrolls`
- `avg_trends_walmart`
- `avg_trends_grocery_store`
- `avg_trends_discount_store`
- `avg_trends_cleaning_supplies`
- `distinct_items`
- `distinct_stores`

Notes:
- much smaller than the row-level mart
- ideal for executive and overview pages

---

### 3. `dashboard_store_item_daily`
Purpose:
- support Store / Item Drilldown
- support detailed row-level operational analysis

Grain:
- original mart grain (`item-store-day` / `id-date`)

Fields:
- keep the existing feature mart columns needed by drilldown and detailed tables

Notes:
- this is the only large serving extract
- load only when drilldown/detail pages need it
- should not be the default dataset used to populate the whole app shell

---

### 4. `dashboard_pipeline_health`
Purpose:
- support Data Quality & Freshness page

Sources:
- audit ingestion runs
- audit DQ runs

Notes:
- should be exported separately from the feature mart

## Loading strategy in Streamlit

### Default app load
Load only:
- `dashboard_filter_options`
- `dashboard_exec_daily`

### Drilldown page load
Load:
- `dashboard_store_item_daily`
only when the drilldown page is selected

### Health page load
Load:
- `dashboard_pipeline_health`

## Why this design

This keeps the dashboard:

- faster
- cheaper to run
- less memory-heavy
- easier to deploy outside AWS
- robust for Streamlit / Hugging Face / future frontend migration

It also avoids using a 2.7M-row dataset as the default source for every page and every filter render.