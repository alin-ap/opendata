# Official Producers

This directory contains "official" dataset producers used for cold-start.

Each producer is a self-contained folder with:

- `opendata.yaml` (metadata)
- `main.py` (producer entrypoint; writes `out/data.parquet`)
- `README.md` (dataset description)

Run one producer locally:

```bash
python main.py
```

Then publish to local storage:

```bash
export OPENDATA_STORAGE=local
export OPENDATA_LOCAL_STORAGE_DIR=.opendata/storage

VERSION=$(date -u +%Y-%m-%d)
od push <dataset_id> out/data.parquet --version "$VERSION"
od registry add opendata.yaml --refresh
```

Current datasets:

- `official/binance-btcusdt-kline-1m`
- `official/stooq-aapl-daily`
- `official/open-meteo-berlin-hourly`
- `official/owid-covid-global-daily`
