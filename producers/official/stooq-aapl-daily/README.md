# Stooq AAPL Daily

Source: Stooq CSV endpoint.

This producer downloads the full daily history for `AAPL.US` and writes it to `out/data.parquet`.

Columns:

- `date` (UTC date)
- `open`, `high`, `low`, `close`
- `volume`
- `symbol`
