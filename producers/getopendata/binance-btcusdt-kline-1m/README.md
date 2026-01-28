# Binance BTCUSDT 1m Kline

Source: Binance Spot API `GET /api/v3/klines`.

This producer fetches a rolling window of the last ~24 hours of 1-minute candles for `BTCUSDT`
and publishes them to R2 as Parquet.

Notes:

- Upstream data availability and rate limits are controlled by Binance.
- The dataset version is expected to be the UTC publish date (`YYYY-MM-DD`).
