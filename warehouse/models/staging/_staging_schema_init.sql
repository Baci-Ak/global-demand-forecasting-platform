{{ config(materialized='view', schema=env_var('STAGING_SCHEMA', 'staging')) }}

select 1 as _staging_schema_initialized
