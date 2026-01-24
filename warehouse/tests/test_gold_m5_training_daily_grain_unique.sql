-- ------------------------------------------------------------------------------
-- Gold contract test: training grain uniqueness
--
-- The Gold training dataset must be unique at grain:
--   (store_id, item_id, date)
--
-- If this fails, downstream feature engineering and model training can silently
-- double-count rows (data leakage / incorrect targets).
-- ------------------------------------------------------------------------------

select
    store_id,
    item_id,
    date,
    count(*) as row_count
from {{ ref('gold_m5_training_daily') }}
group by 1, 2, 3
having count(*) > 1
