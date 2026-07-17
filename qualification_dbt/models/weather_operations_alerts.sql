select
  city,
  observed_date,
  case
    when wind_speed_kph >= 30 then 'high_wind'
    when precipitation_mm >= 7 then 'heavy_rain'
    when temperature_c >= 24 then 'warm'
    else 'normal'
  end as operations_state
from {{ ref('stg_weather_observations') }}
