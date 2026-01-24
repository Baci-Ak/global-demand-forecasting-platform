-- ------------------------------------------------------------------------------
-- Gold guardrail: sales must be non-negative
--
-- For M5 daily unit sales, negative values should not exist in the training set.
-- If this fails, something upstream is broken (bad cast, join duplication,
-- incorrect aggregation, or corrupted raw data).
-- ------------------------------------------------------------------------------

select *
from {{ ref('gold_m5_training_daily') }}
where sales < 0
