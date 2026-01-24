# FRED UNRATE (Unemployment Rate)

Source: FRED series `UNRATE`.

This producer downloads the public CSV export and publishes it to R2 as Parquet.

Columns:

- `date` (UTC timestamp)
- `value` (float)
- `series_id` (string)
