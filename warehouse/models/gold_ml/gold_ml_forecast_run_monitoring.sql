{{ config(materialized='view') }}

select
    generated_at,
    model_name,
    model_version,
    feature_set_name,
    min(forecast_date) as min_forecast_date,
    max(forecast_date) as max_forecast_date,
    count(*) as forecast_row_count,
    count(distinct store_id || '|' || item_id) as forecast_series_count
from forecast.daily_item_store_forecasts
group by
    generated_at,
    model_name,
    model_version,
    feature_set_name