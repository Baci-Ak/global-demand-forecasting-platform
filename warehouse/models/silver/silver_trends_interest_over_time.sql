{{ config(materialized='table') }}

-- ------------------------------------------------------------------------------
-- silver_trends_interest_over_time
--
-- Purpose
-- -------
-- Clean and type raw Google Trends interest-over-time observations from staging
-- into a stable Silver model for downstream feature joins.
--
-- Notes
-- -----
-- - Keep one row per (feature_name, trend_date).
-- - Interest values are expected to be numeric in the 0-100 range.
-- ------------------------------------------------------------------------------

with src as (

    select
        ingest_date::date as ingest_date,
        source_name,
        provider,
        schema_version,
        keyword,
        feature_name,
        label,
        geo,
        trend_date::date as trend_date,
        interest_value::int as interest_value

    from {{ source('staging', 'trends_interest_over_time_raw') }}

)

select *
from src
where feature_name is not null
  and trend_date is not null