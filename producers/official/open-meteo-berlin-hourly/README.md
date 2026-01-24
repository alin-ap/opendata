# Open-Meteo Berlin Hourly

Source: Open-Meteo public API.

This producer fetches hourly data for Berlin (UTC timezone) for the past 7 days and writes
it to R2 as Parquet via the `opendata` SDK.

Selected variables:

- `temperature_2m`
- `relative_humidity_2m`
- `precipitation`
- `wind_speed_10m`
