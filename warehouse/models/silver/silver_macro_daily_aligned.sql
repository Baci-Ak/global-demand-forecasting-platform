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
-- - First build the stable feature domain from macro series metadata.
-- - For each (date, feature_name), carry forward the most recent available
--   macro observation on or before that date.
-- - Output grain:
--     (date, feature_name)
--
-- Important behavior
-- ------------------
-- - This model never emits rows with null feature_name.
-- - Dates earlier than the first available observation for a feature simply
--   do not produce an aligned row for that feature.
-- ------------------------------------------------------------------------------

with sales_dates as (

    select distinct
        date
    from {{ ref('silver_m5_sales') }}

),

macro_features as (

    select distinct
        feature_name
    from {{ ref('silver_macro_series') }}
    where feature_name is not null

),

macro as (

    select
        feature_name,
        observation_date,
        observation_value
    from {{ ref('silver_macro_series') }}
    where observation_value is not null
      and feature_name is not null

),

date_feature_spine as (

    select
        s.date,
        f.feature_name
    from sales_dates s
    cross join macro_features f

),

joined as (

    select
        s.date,
        s.feature_name,
        m.observation_date,
        m.observation_value,
        row_number() over (
            partition by s.date, s.feature_name
            order by m.observation_date desc
        ) as rn
    from date_feature_spine s
    left join macro m
      on m.feature_name = s.feature_name
     and m.observation_date <= s.date

)

select
    date,
    feature_name,
    observation_date as source_observation_date,
    observation_value
from joined
where rn = 1
  and observation_date is not null