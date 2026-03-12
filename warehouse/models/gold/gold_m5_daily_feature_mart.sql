{{ config(materialized='table') }}

-- ------------------------------------------------------------------------------
-- gold_m5_daily_feature_mart
--
-- Purpose
-- -------
-- Final business-ready and ML-ready daily training dataset for demand
-- forecasting, BI, and downstream analytics.
--
-- Grain
-- -----
-- One row per:
--   (store_id, item_id, date)
--
-- Sources
-- -------
-- Built from:
-- - silver_m5_sales_with_external_features
-- - silver_m5_sales_with_prices
--
-- Design principles
-- -----------------
-- - Keep a stable, analyst-friendly daily fact table.
-- - Include core commercial context such as price and retail week.
-- - Include external feature families already integrated in Silver:
--     • Weather
--     • Macro
--     • Google Trends
-- ------------------------------------------------------------------------------

with base as (

    select
        id,
        item_id,
        dept_id,
        cat_id,
        store_id,
        state_id,
        d,
        date,
        sales,
        temperature_2m_max,
        temperature_2m_min,
        precipitation_sum,
        wind_speed_10m_max,
        cpi_all_items,
        unemployment_rate,
        federal_funds_rate,
        nonfarm_payrolls,
        trends_walmart,
        trends_grocery_store,
        trends_discount_store,
        trends_cleaning_supplies
    from {{ ref('silver_m5_sales_with_external_features') }}

),

pricing as (

    select
        store_id,
        item_id,
        date,
        wm_yr_wk,
        sell_price
    from {{ ref('silver_m5_sales_with_prices') }}

)

select
    b.id,
    b.item_id,
    b.dept_id,
    b.cat_id,
    b.store_id,
    b.state_id,
    b.d,
    b.date,
    p.wm_yr_wk,
    b.sales,
    p.sell_price,

    -- Weather features
    b.temperature_2m_max,
    b.temperature_2m_min,
    b.precipitation_sum,
    b.wind_speed_10m_max,

    -- Macro features
    b.cpi_all_items,
    b.unemployment_rate,
    b.federal_funds_rate,
    b.nonfarm_payrolls,

    -- Trends features
    b.trends_walmart,
    b.trends_grocery_store,
    b.trends_discount_store,
    b.trends_cleaning_supplies

from base b
left join pricing p
  on b.store_id = p.store_id
 and b.item_id = p.item_id
 and b.date = p.date