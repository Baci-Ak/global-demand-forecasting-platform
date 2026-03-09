{{ config(materialized='table') }}

-- ------------------------------------------------------------------------------
-- gold_m5_training_daily_with_macro
--
-- Purpose
-- -------
-- Gold daily training dataset at grain (store_id, item_id, date), built from
-- Silver sales enriched with aligned macroeconomic features.
--
-- Notes
-- -----
-- - Keep the output narrow and stable for downstream training use.
-- - Macro features are date-level context shared across all sales rows for the
--   same day.
-- ------------------------------------------------------------------------------

select
    store_id,
    item_id,
    date,
    state_id,
    cat_id,
    dept_id,
    sales,
    cpi_all_items,
    unemployment_rate,
    federal_funds_rate,
    nonfarm_payrolls
from {{ ref('silver_m5_sales_with_macro') }}