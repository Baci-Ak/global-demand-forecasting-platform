{{ config(materialized='table') }}

-- ------------------------------------------------------------------------------
-- gold_m5_training_daily
--
-- Purpose
-- -------
-- Gold (feature-ready) daily training dataset at the grain:
--   (store_id, item_id, date)
--
-- Built from Silver daily sales enriched with weekly prices.
-- This table is intended as the primary input for forecasting feature engineering.
--
-- Notes
-- -----
-- - Local dev uses a limited sales history window (loader MAX_D_COLS).
-- - In production this becomes full-history (and likely incremental).
-- ------------------------------------------------------------------------------

select
    store_id,
    item_id,
    date,
    state_id,
    cat_id,
    dept_id,
    wm_yr_wk,
    sales,
    sell_price
from {{ ref('silver_m5_sales_with_prices') }}
