select
  observed_date,
  count(distinct city) as reporting_city_count,
  round(avg(temperature_c), 2) as average_temperature_c,
  round(sum(precipitation_mm), 2) as total_precipitation_mm,
  round(max(wind_speed_kph), 2) as maximum_wind_speed_kph
from {{ ref('stg_weather_observations') }}
group by observed_date
