{{ config(materialized='table') }}

-- ------------------------------------------------------------------------------
-- silver_m5_sales
--
-- Purpose
-- -------
-- Daily unit sales fact table in Silver.
--
-- Source
-- ------
-- staging.m5_sales_train_validation_long_raw (loaded by Python in long form)
--
-- Enrichment
-- ----------
-- Join to silver_m5_calendar on `d` to attach the real calendar `date`.
--
-- Notes
-- -----
-- In local dev we may only load the last N days into staging (see loader).
-- In production, this model works the same; it will simply contain full history.
-- ------------------------------------------------------------------------------

with sales as (

    -- Base sales grain: one row per (id, d)
    select
        id,
        item_id,
        dept_id,
        cat_id,
        store_id,
        state_id,
        d,
        sales::int as sales
    from {{ source('staging', 'm5_sales_train_validation_long_raw') }}

),

cal as (

    -- Calendar dimension: map `d` -> actual date
    select
        d,
        date
    from {{ ref('silver_m5_calendar') }}

)

-- Final curated daily sales fact table
select
    s.id,
    s.item_id,
    s.dept_id,
    s.cat_id,
    s.store_id,
    s.state_id,
    s.d,
    c.date,
    s.sales
from sales s
left join cal c
  using (d)
where s.sales >= 0
  and c.date is not null
