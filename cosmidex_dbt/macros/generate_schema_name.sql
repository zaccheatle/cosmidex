{#
    Override dbt's default schema naming so custom schemas (staging, marts) are
    used as-is, rather than prefixed with the target schema name.
#}
{% macro generate_schema_name(custom_schema_name, node) %}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{% endmacro %}
