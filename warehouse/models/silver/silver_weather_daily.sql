{{ config(materialized='table') }}

with src as (

    select
        ingest_date::date as ingest_date,
        source_name,
        provider,
        schema_version,
        location_id,
        state_id,
        location_label,
        location_timezone,
        latitude::double precision as latitude,
        longitude::double precision as longitude,
        weather_date::date as weather_date,
        temperature_2m_max::double precision as temperature_2m_max,
        temperature_2m_min::double precision as temperature_2m_min,
        precipitation_sum::double precision as precipitation_sum,
        wind_speed_10m_max::double precision as wind_speed_10m_max

    from {{ source('staging', 'weather_daily_raw') }}

)

select *
from src
where location_id is not null
  and state_id is not null
  and weather_date is not null