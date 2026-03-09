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
-- - Join external features strictly on the sales date.
-- - Each feature family is pre-aligned to the sales date set upstream.
--
-- Downstream usage
-- ----------------
-- This table becomes the canonical feature source for forecasting models
-- and feeds the Gold training dataset.
-- ------------------------------------------------------------------------------

with sales as (

    select *
    from {{ ref('silver_m5_sales') }}

),

weather as (

    select
        id,
        date,
        temperature_2m_max,
        temperature_2m_min,
        precipitation_sum,
        wind_speed_10m_max
    from {{ ref('silver_m5_sales_with_weather') }}

),

macro as (

    select
        id,
        date,
        cpi_all_items,
        unemployment_rate,
        federal_funds_rate,
        nonfarm_payrolls
    from {{ ref('silver_m5_sales_with_macro') }}

),

trends as (

    select
        id,
        date,
        trends_walmart,
        trends_grocery_store,
        trends_discount_store,
        trends_cleaning_supplies
    from {{ ref('silver_m5_sales_with_trends') }}

)

select
    s.*,

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
  on s.id = w.id
 and s.date = w.date

left join macro m
  on s.id = m.id
 and s.date = m.date

left join trends t
  on s.id = t.id
 and s.date = t.date