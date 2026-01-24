# Official Producers

This directory contains "official" dataset producers used for cold-start.

Each producer is a self-contained folder with:

- `opendata.yaml` (metadata)
- `main.py` (producer entrypoint; publishes to R2 via the SDK)
- `README.md` (dataset description)

Run one producer locally (publishes to local storage by default):

```bash
python main.py
```

Batch publish all official datasets:

```bash
export OPENDATA_STORAGE=local
export OPENDATA_LOCAL_STORAGE_DIR=.opendata/storage

VERSION=$(date -u +%Y-%m-%d)
python3 scripts/publish_official_local.py --version "$VERSION" --ignore-failures
```

Current datasets:

- `official/binance-btcusdt-kline-1m`
- `official/coinbase-btc-usd-candles-1d`
- `official/coinbase-eth-usd-candles-1d`
- `official/coingecko-btc-usd-market-daily`
- `official/coingecko-eth-usd-market-daily`
- `official/ecb-eurofxref-hist`
- `official/fred-cpi-u-monthly`
- `official/fred-fedfunds-monthly`
- `official/fred-unrate-monthly`
- `official/open-meteo-berlin-hourly`
- `official/owid-covid-global-daily`
- `official/stooq-aapl-daily`
- `official/usgs-earthquakes-all-day`
