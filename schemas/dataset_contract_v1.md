# Dataset Contract (v1)

This document defines the **wire contract** between producers, storage (R2), the registry
index, and consumers.

The goal is that any dataset published by any producer is:

- predictable (stable object keys)
- auditable (metadata + checksums + schema)
- cheap to serve (portal + consumers read from R2 directly)

## 1) Identifiers

### Dataset ID

- Format: `namespace/name`
- Regex: `^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*$`
- Examples:
  - `official/stooq-aapl-daily`
  - `official/fred-unrate-monthly`

Dataset IDs are canonical and used to derive storage keys.

### Version

- A single version string per published snapshot.
- Regex: `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$` (no slashes)
- Default for official producers: UTC date `YYYY-MM-DD`.

## 2) Storage layout (R2 keys)

All objects must live under a predictable prefix:

```
datasets/<namespace>/<name>/<version>/data.parquet
datasets/<namespace>/<name>/<version>/schema.json
datasets/<namespace>/<name>/<version>/preview.json
datasets/<namespace>/<name>/latest.json
datasets/<namespace>/<name>/README.md
```

Notes:

- `data.parquet` is the canonical dataset payload.
- `latest.json` is a small pointer describing the newest published version.
- `preview.json` is precomputed head rows for the portal (avoid online compute).
- `README.md` is stable per dataset (human documentation).

## 3) JSON schemas

### schema.json

```json
{
  "format": "parquet",
  "columns": [
    {"name": "date", "type": "timestamp[ns, tz=UTC]"},
    {"name": "value", "type": "double"}
  ]
}
```

### preview.json

```json
{
  "dataset_id": "official/fred-unrate-monthly",
  "version": "2026-01-24",
  "generated_at": "2026-01-24T19:07:54+00:00",
  "columns": ["date", "value", "series_id"],
  "rows": [
    {"date": "1948-01-01T00:00:00+00:00", "value": 3.4, "series_id": "UNRATE"}
  ]
}
```

Rules:

- `rows` must be a JSON array of objects.
- timestamps should be ISO-8601 strings.

### latest.json

```json
{
  "dataset_id": "official/fred-unrate-monthly",
  "version": "2026-01-24",
  "updated_at": "2026-01-24T19:07:54+00:00",
  "data_key": "datasets/official/fred-unrate-monthly/2026-01-24/data.parquet",
  "schema_key": "datasets/official/fred-unrate-monthly/2026-01-24/schema.json",
  "preview_key": "datasets/official/fred-unrate-monthly/2026-01-24/preview.json",
  "row_count": 936,
  "data_size_bytes": 12137,
  "checksum_sha256": "...",
  "schema_hash_sha256": "..."
}
```

### index.json

The registry index is a single searchable list.

```json
{
  "meta_version": 1,
  "generated_at": "2026-01-24T19:08:09+00:00",
  "datasets": [
    {
      "id": "official/fred-unrate-monthly",
      "title": "FRED UNRATE (Unemployment Rate)",
      "description": "US unemployment rate (monthly) from FRED.",
      "license": "unknown",
      "source": "https://fred.stlouisfed.org/series/UNRATE",
      "repo": "https://github.com/getopendata/getopendata",
      "readme_key": "datasets/official/fred-unrate-monthly/README.md",
      "tags": ["macro", "fred", "unemployment"],
      "owners": ["alin"],
      "frequency": "monthly",
      "versioning": "date",

      "version": "2026-01-24",
      "updated_at": "2026-01-24T19:07:54+00:00",
      "data_key": "datasets/official/fred-unrate-monthly/2026-01-24/data.parquet",
      "schema_key": "datasets/official/fred-unrate-monthly/2026-01-24/schema.json",
      "preview_key": "datasets/official/fred-unrate-monthly/2026-01-24/preview.json",
      "row_count": 936,
      "data_size_bytes": 12137
    }
  ]
}
```

## 4) Producer contract

An official producer lives at `producers/official/<slug>/` and must contain:

- `opendata.yaml` (metadata, `meta_version: 1`)
- `README.md`
- `main.py`

Producer runtime contract:

- `main.py` should produce a pandas DataFrame or Arrow table.
- It should publish directly via the SDK (no `out/data.parquet` contract):

```python
from pathlib import Path
import pandas as pd
from opendata.producer import publish_dataframe_from_dir

producer_dir = Path(__file__).resolve().parent
df = pd.DataFrame(...)
publish_dataframe_from_dir(producer_dir, df=df)
```

Environment variables used by producers:

- `OPENDATA_STORAGE`: `local` | `r2` (default: `local`)
- `OPENDATA_VERSION`: version string (typically set by CI)
- `OPENDATA_PREVIEW_ROWS`: preview row count (default: 100)

## 5) Independence

- Each dataset publishes only to its own key prefix.
- The global `index.json` should be rebuilt once after all producers run
  (avoid concurrent writes).
