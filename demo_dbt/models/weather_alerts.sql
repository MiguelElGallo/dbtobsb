select
  city,
  observed_date,
  case
    when precipitation_mm >= 7 then 'heavy_rain'
    when temperature_c >= 24 then 'warm'
    else 'normal'
  end as weather_state
from {{ ref('stg_weather') }}
