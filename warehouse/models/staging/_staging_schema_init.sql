{{ config(materialized='view', schema='staging') }}

select 1 as _staging_schema_initialized
