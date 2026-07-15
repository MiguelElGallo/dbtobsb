{{ config(tags=["observed"]) }}

select
  1 as fixture_id,
  cast('2026-01-01' as timestamp) as created_at
