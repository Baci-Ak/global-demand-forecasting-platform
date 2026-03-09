{{ config(materialized='table') }}

-- ------------------------------------------------------------------------------
-- silver_macro_daily_aligned
--
-- Purpose
-- -------
-- Align lower-frequency macroeconomic observations to the actual daily sales
-- dates used by M5 so downstream feature models can join on `date`.
--
-- Design
-- ------
-- - Start from the actual sales date set, not the full calendar table.
-- - For each sales date and macro feature, carry forward the most recent
--   available macro observation on or before that date.
-- - Output grain:
--     (date, feature_name)
--
-- Notes
-- -----
-- - This keeps the aligned macro table scoped to the real training horizon.
-- - Later, if needed, we can replace this with release-aware or vintage-aware
--   logic without changing downstream model interfaces.
-- ------------------------------------------------------------------------------

with sales_dates as (

    select distinct
        date
    from {{ ref('silver_m5_sales') }}

),

macro as (

    select
        feature_name,
        observation_date,
        observation_value
    from {{ ref('silver_macro_series') }}
    where observation_value is not null

),

joined as (

    select
        s.date,
        m.feature_name,
        m.observation_date,
        m.observation_value,
        row_number() over (
            partition by s.date, m.feature_name
            order by m.observation_date desc
        ) as rn
    from sales_dates s
    left join macro m
      on m.observation_date <= s.date

)

select
    date,
    feature_name,
    observation_date as source_observation_date,
    observation_value
from joined
where rn = 1