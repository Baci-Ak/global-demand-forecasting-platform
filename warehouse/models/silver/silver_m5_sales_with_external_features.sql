{{ config(materialized='table') }}

-- ------------------------------------------------------------------------------
-- silver_m5_sales_with_external_features
--
-- Purpose
-- -------
-- Unified Silver integration model combining all external feature sources with
-- daily M5 sales.
--
-- External feature families
-- -------------------------
-- • Weather
-- • Macro
-- • Google Trends
--
-- Design
-- ------
-- - Preserve the original M5 sales grain.
-- - Join weather by (state_id, date).
-- - Join macro and trends by date after upstream daily alignment.
-- - Avoid depending on redundant intermediate "sales_with_*" models.
--
-- Output grain
-- ------------
-- One row per:
--   (id, d)
-- which maps to daily sales grain:
--   (store_id, item_id, date)
-- ------------------------------------------------------------------------------

with sales as (

    select
        id,
        item_id,
        dept_id,
        cat_id,
        store_id,
        state_id,
        d,
        date,
        sales
    from {{ ref('silver_m5_sales') }}

),

weather as (

    select
        state_id,
        weather_date,
        temperature_2m_max,
        temperature_2m_min,
        precipitation_sum,
        wind_speed_10m_max
    from {{ ref('silver_weather_daily') }}

),

macro as (

    select
        date,
        max(case when feature_name = 'cpi_all_items' then observation_value end) as cpi_all_items,
        max(case when feature_name = 'unemployment_rate' then observation_value end) as unemployment_rate,
        max(case when feature_name = 'federal_funds_rate' then observation_value end) as federal_funds_rate,
        max(case when feature_name = 'nonfarm_payrolls' then observation_value end) as nonfarm_payrolls
    from {{ ref('silver_macro_daily_aligned') }}
    group by date

),

trends as (

    select
        date,
        max(case when feature_name = 'trends_walmart' then interest_value end) as trends_walmart,
        max(case when feature_name = 'trends_grocery_store' then interest_value end) as trends_grocery_store,
        max(case when feature_name = 'trends_discount_store' then interest_value end) as trends_discount_store,
        max(case when feature_name = 'trends_cleaning_supplies' then interest_value end) as trends_cleaning_supplies
    from {{ ref('silver_trends_daily_aligned') }}
    group by date

)

select
    s.id,
    s.item_id,
    s.dept_id,
    s.cat_id,
    s.store_id,
    s.state_id,
    s.d,
    s.date,
    s.sales,

    -- Weather features
    w.temperature_2m_max,
    w.temperature_2m_min,
    w.precipitation_sum,
    w.wind_speed_10m_max,

    -- Macro features
    m.cpi_all_items,
    m.unemployment_rate,
    m.federal_funds_rate,
    m.nonfarm_payrolls,

    -- Trends features
    t.trends_walmart,
    t.trends_grocery_store,
    t.trends_discount_store,
    t.trends_cleaning_supplies

from sales s
left join weather w
  on s.state_id = w.state_id
 and s.date = w.weather_date
left join macro m
  on s.date = m.date
left join trends t
  on s.date = t.date