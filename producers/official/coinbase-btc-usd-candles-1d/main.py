from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

from opendata.producer import publish_dataframe_from_dir

PRODUCT_ID = "BTC-USD"
GRANULARITY = 86400
URL = f"https://api.exchange.coinbase.com/products/{PRODUCT_ID}/candles"


def main() -> None:
    producer_dir = Path(__file__).resolve().parent

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=300)

    params = {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "granularity": GRANULARITY,
    }
    resp = requests.get(URL, params=params, timeout=60)
    resp.raise_for_status()
    rows = resp.json()

    df = pd.DataFrame(rows, columns=["time_s", "low", "high", "open", "close", "volume"])
    df["time"] = pd.to_datetime(df.pop("time_s"), unit="s", utc=True)
    for c in ["low", "high", "open", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.sort_values("time").reset_index(drop=True)
    df["product_id"] = PRODUCT_ID
    df["granularity"] = GRANULARITY

    published = publish_dataframe_from_dir(producer_dir, df=df)
    print(json.dumps(published.latest_pointer(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
