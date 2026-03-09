{{ config(materialized='table') }}

-- ------------------------------------------------------------------------------
-- silver_trends_daily_aligned
--
-- Purpose
-- -------
-- Align Google Trends observations to the actual daily sales dates used by M5
-- so downstream feature models can join on `date`.
--
-- Design
-- ------
-- - Start from the actual sales date set, not the full calendar table.
-- - Keep one row per (date, feature_name).
-- - Trends is already daily, so this is primarily a scoping/alignment model.
-- ------------------------------------------------------------------------------

with sales_dates as (

    select distinct
        date
    from {{ ref('silver_m5_sales') }}

),

trends as (

    select
        feature_name,
        trend_date,
        interest_value
    from {{ ref('silver_trends_interest_over_time') }}

)

select
    s.date,
    t.feature_name,
    t.trend_date as source_trend_date,
    t.interest_value
from sales_dates s
left join trends t
  on s.date = t.trend_date
where t.feature_name is not null