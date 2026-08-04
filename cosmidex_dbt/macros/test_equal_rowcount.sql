{#
    Generic test: fails if model and compare_model don't have the same row count.
    Written in-house to avoid a dbt_utils dependency for this one test.
#}
{% test equal_rowcount(model, compare_model) %}

    with model_count as (
        select count(*) as row_count from {{ model }}
    ),

    compare_count as (
        select count(*) as row_count from {{ compare_model }}
    )

    select
        model_count.row_count as actual_row_count,
        compare_count.row_count as expected_row_count
    from model_count
    cross join compare_count
    where model_count.row_count != compare_count.row_count

{% endtest %}
