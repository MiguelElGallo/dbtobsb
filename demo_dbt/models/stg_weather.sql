select
  cast(city as string) as city,
  cast(observed_date as date) as observed_date,
  cast(temperature_c as decimal(5, 2)) as temperature_c,
  cast(precipitation_mm as decimal(7, 2)) as precipitation_mm
from {{ ref('weather_observations') }}
