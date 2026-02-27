{{ config(materialized='table') }}

-- ------------------------------------------------------------------------------
-- silver_m5_sales_with_prices
--
-- Purpose
-- -------
-- Training-ready daily fact table that enriches daily unit sales with weekly sell
-- prices by joining on (store_id, item_id, wm_yr_wk).
--
-- Inputs
-- ------
-- - silver_m5_sales: daily sales with real calendar date
-- - silver_m5_calendar: provides wm_yr_wk for each date via `d`
-- - silver_m5_sell_prices: weekly sell prices at (store_id, item_id, wm_yr_wk)
--
-- Notes
-- -----
-- Prices are weekly. We attach the weekly price corresponding to the calendar
-- week of each daily sales row.
-- ------------------------------------------------------------------------------

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

cal as (

    -- bring wm_yr_wk onto each day
    select
        d,
        wm_yr_wk
    from {{ ref('silver_m5_calendar') }}

),

prices as (

    select
        store_id,
        item_id,
        wm_yr_wk,
        sell_price
    from {{ ref('silver_m5_sell_prices') }}

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
    c.wm_yr_wk,
    s.sales,
    p.sell_price
from sales s
left join cal c
  using (d)
left join prices p
  on  p.store_id = s.store_id
  and p.item_id = s.item_id
  and p.wm_yr_wk = c.wm_yr_wk

