{#
    Generic test: fails if any non-null value in column_name falls outside
    [min_value, max_value]. Either bound may be omitted for a one-sided check.
    Written in-house to avoid a dbt_utils dependency for this one test.
#}
{% test accepted_range(model, column_name, min_value=none, max_value=none) %}

    select *
    from {{ model }}
    where {{ column_name }} is not null
    {% if min_value is not none %}
    and {{ column_name }} < {{ min_value }}
    {% endif %}
    {% if max_value is not none %}
    and {{ column_name }} > {{ max_value }}
    {% endif %}

{% endtest %}
