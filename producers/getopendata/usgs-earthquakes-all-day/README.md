# USGS Earthquakes (All Day)

Source: USGS GeoJSON earthquake feeds.

This producer downloads the `all_day` feed (last 24 hours) and publishes it to R2 as Parquet.

Columns (subset):

- `event_id`
- `time` (UTC timestamp)
- `updated_at` (UTC timestamp)
- `mag`
- `place`
- `tsunami`
- `longitude`, `latitude`, `depth_km`
- `url`
