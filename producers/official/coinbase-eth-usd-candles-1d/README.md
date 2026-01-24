# Coinbase ETH-USD Candles (1d)

Source: Coinbase Exchange API `GET /products/<product-id>/candles`.

This producer fetches the last ~300 daily candles for `ETH-USD` and publishes them to R2 as Parquet.

Columns:

- `time` (UTC timestamp)
- `low`, `high`, `open`, `close`, `volume`
- `product_id`
- `granularity` (seconds)
