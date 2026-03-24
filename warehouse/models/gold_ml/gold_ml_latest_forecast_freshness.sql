{{ config(materialized='view') }}

with latest_run as (
    select max(generated_at) as latest_generated_at
    from forecast.daily_item_store_forecasts
),

latest_forecasts as (
    select f.*
    from forecast.daily_item_store_forecasts f
    join latest_run r
      on f.generated_at = r.latest_generated_at
)

select
    generated_at,
    model_name,
    model_version,
    feature_set_name,
    min(forecast_date) as min_forecast_date,
    max(forecast_date) as max_forecast_date,
    count(*) as forecast_row_count,
    count(distinct store_id || '|' || item_id) as forecast_series_count,
    datediff(day, min(forecast_date), max(forecast_date)) + 1 as forecast_horizon_days
from latest_forecasts
group by
    generated_at,
    model_name,
    model_version,
    feature_set_name