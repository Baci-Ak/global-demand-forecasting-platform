-- Fail if more than 20% of rows are missing sell_price.
-- (We expect some missingness, but not extreme if joins are correct.)

with stats as (
    select
        count(*) as total_rows,
        sum(case when sell_price is null then 1 else 0 end) as null_prices
    from {{ ref('silver_m5_sales_with_prices') }}
)

select 1
from stats
where (null_prices::float / nullif(total_rows, 0)) > 0.20
