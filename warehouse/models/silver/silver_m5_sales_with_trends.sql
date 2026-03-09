{{ config(materialized='table') }}

-- ------------------------------------------------------------------------------
-- silver_m5_sales_with_trends
--
-- Purpose
-- -------
-- Enrich daily M5 sales with aligned Google Trends search-intent features.
--
-- Design
-- ------
-- - Base grain remains one row per sales record in silver_m5_sales.
-- - Trends features are joined by date after being aligned to the M5 sales date set.
-- - We pivot the curated Trends feature set into explicit columns for a stable
--   downstream contract.
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

trends as (

    select
        date,
        max(case when feature_name = 'trends_walmart' then interest_value end) as trends_walmart,
        max(case when feature_name = 'trends_grocery_store' then interest_value end) as trends_grocery_store,
        max(case when feature_name = 'trends_discount_store' then interest_value end) as trends_discount_store,
        max(case when feature_name = 'trends_cleaning_supplies' then interest_value end) as trends_cleaning_supplies
    from {{ ref('silver_trends_daily_aligned') }}
    group by date

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
    t.trends_walmart,
    t.trends_grocery_store,
    t.trends_discount_store,
    t.trends_cleaning_supplies
from sales s
left join trends t
  on s.date = t.date