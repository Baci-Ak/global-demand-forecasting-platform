{{ config(materialized='table') }}

-- ------------------------------------------------------------------------------
-- silver_macro_series
--
-- Purpose
-- -------
-- Clean and type raw macroeconomic observations from staging into a stable
-- Silver model for downstream feature joins.
--
-- Notes
-- -----
-- - Keep one row per (series_id, observation_date).
-- - Observation values from FRED arrive as strings, so we null out "." and cast.
-- ------------------------------------------------------------------------------

with src as (

    select
        ingest_date::date as ingest_date,
        source_name,
        provider,
        schema_version,
        series_id,
        feature_name,
        series_label,
        frequency,
        units,
        observation_date::date as observation_date,
        nullif(observation_value, '.')::numeric as observation_value

    from {{ source('staging', 'macro_series_raw') }}

)

select *
from src
where series_id is not null
  and feature_name is not null
  and observation_date is not null