{{ config(materialized='table') }}

-- ------------------------------------------------------------------------------
-- gold_forecasts_top20
--
-- Purpose
-- -------
-- Publish the current benchmark forecast artifact into the warehouse-facing Gold
-- layer for downstream analytics, dashboarding, and API access.
--
-- Grain
-- -----
-- One row per:
--   (store_id, item_id, forecast_date, forecast_step)
--
-- Notes
-- -----
-- - This is the first warehouse-facing forecast table for the benchmark subset.
-- - It will later be replaced or extended by a production full-scope forecast table.
-- - The upstream parquet artifact is produced by:
--     python -m training.predict_next_28_days
-- ------------------------------------------------------------------------------

select
    cast(store_id as text) as store_id,
    cast(item_id as text) as item_id,
    cast(forecast_date as date) as forecast_date,
    cast(forecast_step as integer) as forecast_step,
    cast(prediction as numeric(18,6)) as prediction
from {{ source('external', 'top20_next_28_days_forecast') }}