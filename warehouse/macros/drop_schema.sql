{% macro drop_schema(schema_name) %}
  {% set sql %}
    drop schema if exists {{ schema_name }} cascade;
  {% endset %}
  {% do run_query(sql) %}
{% endmacro %}
