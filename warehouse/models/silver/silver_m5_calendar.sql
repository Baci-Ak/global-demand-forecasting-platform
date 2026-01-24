{{ config(materialized='table') }}

with src as (

    select
        d,
        date::date as date,
        wm_yr_wk::int as wm_yr_wk,
        weekday,

        extract(year from date::date)::int  as year,
        extract(month from date::date)::int as month,
        extract(day from date::date)::int   as day,

        -- Postgres: 1=Sunday..7=Saturday, convert to ISO 1=Mon..7=Sun
        ((extract(dow from date::date)::int + 6) % 7) + 1 as day_of_week

    from {{ source('staging', 'm5_calendar_raw') }}

)

select *
from src
where d is not null
  and date is not null
  and wm_yr_wk is not null
    and weekday is not null

