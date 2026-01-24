# Stooq AAPL Daily

Source: Stooq CSV endpoint.

This producer downloads the full daily history for `AAPL.US` and publishes it to R2 as Parquet.

Columns:

- `date` (UTC date)
- `open`, `high`, `low`, `close`
- `volume`
- `symbol`
