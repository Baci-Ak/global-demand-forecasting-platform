{{ config(materialized='table') }}

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
    w.temperature_2m_max,
    w.temperature_2m_min,
    w.precipitation_sum,
    w.wind_speed_10m_max
from sales s
left join weather w
  on  s.state_id = w.state_id
  and s.date = w.weather_date