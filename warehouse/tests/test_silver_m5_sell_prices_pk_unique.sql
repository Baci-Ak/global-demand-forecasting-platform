-- Fail if the composite key (store_id, item_id, wm_yr_wk) is not unique.

select
  store_id,
  item_id,
  wm_yr_wk,
  count(*) as n
from {{ ref('silver_m5_sell_prices') }}
group by 1, 2, 3
having count(*) > 1
