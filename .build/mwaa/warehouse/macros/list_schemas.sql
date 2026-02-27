{% macro debug_list_schemas() %}
  {% set sql %}
    select schema_name
    from information_schema.schemata
    order by schema_name
  {% endset %}

  {% set results = run_query(sql) %}
  {% if execute %}
    {{ log("Schemas in database:", info=True) }}
    {% for row in results.rows %}
      {{ log(row[0], info=True) }}
    {% endfor %}
  {% endif %}
{% endmacro %}
