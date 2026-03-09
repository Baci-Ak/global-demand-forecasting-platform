{{ config(materialized='table') }}

-- ------------------------------------------------------------------------------
-- silver_m5_sales_with_macro
--
-- Purpose
-- -------
-- Enrich daily M5 sales with aligned macroeconomic context.
--
-- Design
-- ------
-- - Base grain remains one row per sales record in silver_m5_sales.
-- - Macro features are joined by date after being aligned to the M5 calendar.
-- - We pivot the small curated macro feature set into explicit columns for a
--   stable downstream contract.
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

macro as (

    select
        date,
        max(case when feature_name = 'cpi_all_items' then observation_value end) as cpi_all_items,
        max(case when feature_name = 'unemployment_rate' then observation_value end) as unemployment_rate,
        max(case when feature_name = 'federal_funds_rate' then observation_value end) as federal_funds_rate,
        max(case when feature_name = 'nonfarm_payrolls' then observation_value end) as nonfarm_payrolls
    from {{ ref('silver_macro_daily_aligned') }}
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
    m.cpi_all_items,
    m.unemployment_rate,
    m.federal_funds_rate,
    m.nonfarm_payrolls
from sales s
left join macro m
  on s.date = m.date