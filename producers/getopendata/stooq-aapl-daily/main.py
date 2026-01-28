from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from opendata.producer import publish_dataframe_from_dir


CATALOG = {
  "id": "getopendata/stooq-aapl-daily",
  "title": "Stooq AAPL Daily",
  "description": "Daily OHLCV history for AAPL.US from Stooq (CSV).",
  "license": "unknown",
  "repo": "https://github.com/getopendata/getopendata",
  "topics": [
    "stocks",
    "ohlcv"
  ],
  "owners": [
    "alin"
  ],
  "frequency": "daily",
  "source": {
    "provider": "stooq",
    "homepage": "https://stooq.com/",
    "dataset": "https://stooq.com/q/d/l/?s=aapl.us&i=d"
  },
  "geo": {
    "scope": "country",
    "countries": [
      "US"
    ]
  }
}

URL = "https://stooq.com/q/d/l/?s=aapl.us&i=d"
SYMBOL = "AAPL.US"


def main() -> None:
    producer_dir = Path(__file__).resolve().parent

    resp = requests.get(URL, timeout=30)
    resp.raise_for_status()

    df = pd.read_csv(StringIO(resp.text))
    df.columns = [c.strip().lower() for c in df.columns]
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], utc=True)

    for c in ["open", "high", "low", "close", "volume"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df["symbol"] = SYMBOL

    published = publish_dataframe_from_dir(producer_dir, df=df, catalog=CATALOG)
    print(json.dumps(published.metadata(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
