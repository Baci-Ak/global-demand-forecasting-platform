{{ config(materialized='table') }}

with src as (

    select
        store_id,
        item_id,
        wm_yr_wk::int as wm_yr_wk,
        sell_price::numeric as sell_price

    from {{ source('staging', 'm5_sell_prices_raw') }}

)

select *
from src
where store_id is not null
  and item_id is not null
  and wm_yr_wk is not null
  and sell_price is not null
  and sell_price > 0
