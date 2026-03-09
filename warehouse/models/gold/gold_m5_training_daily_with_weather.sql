{{ config(materialized='table') }}

select
    store_id,
    item_id,
    date,
    state_id,
    cat_id,
    dept_id,
    sales,
    temperature_2m_max,
    temperature_2m_min,
    precipitation_sum,
    wind_speed_10m_max
from {{ ref('silver_m5_sales_with_weather') }}