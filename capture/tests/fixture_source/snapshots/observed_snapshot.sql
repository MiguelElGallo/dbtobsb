{% snapshot observed_snapshot %}

{{
  config(
    target_schema='fixture_schema',
    unique_key='fixture_id',
    strategy='check',
    check_cols=['fixture_id']
  )
}}

select * from {{ ref('observed_model') }}

{% endsnapshot %}
