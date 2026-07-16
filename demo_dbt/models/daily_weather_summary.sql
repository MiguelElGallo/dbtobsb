select
  observed_date,
  count(distinct city) as city_count,
  round(avg(temperature_c), 2) as average_temperature_c,
  round(sum(precipitation_mm), 2) as total_precipitation_mm
from {{ ref('stg_weather') }}
group by observed_date
