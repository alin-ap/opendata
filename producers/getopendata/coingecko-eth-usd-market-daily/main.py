from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

from opendata.producer import publish_dataframe_from_dir


CATALOG = {
  "id": "getopendata/coingecko-eth-usd-market-daily",
  "title": "CoinGecko ETH Market (Daily)",
  "description": "Daily ETH market price/market cap/volume in USD from CoinGecko (last 365 days).",
  "license": "unknown",
  "repo": "https://github.com/getopendata/getopendata",
  "topics": [
    "crypto",
    "market",
    "eth",
    "usd"
  ],
  "owners": [
    "alin"
  ],
  "frequency": "daily",
  "source": {
    "provider": "coingecko",
    "homepage": "https://www.coingecko.com/",
    "dataset": "https://www.coingecko.com/en/api/documentation"
  }
}

COIN_ID = "ethereum"
URL = f"https://api.coingecko.com/api/v3/coins/{COIN_ID}/market_chart"


def main() -> None:
    producer_dir = Path(__file__).resolve().parent

    params = {"vs_currency": "usd", "days": "365", "interval": "daily"}
    resp = requests.get(URL, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    prices = data.get("prices") or []
    caps = data.get("market_caps") or []
    vols = data.get("total_volumes") or []

    n = min(len(prices), len(caps), len(vols))
    rows = []
    for i in range(n):
        t_ms, p = prices[i]
        _, c = caps[i]
        _, v = vols[i]
        rows.append({"time": t_ms, "price_usd": p, "market_cap_usd": c, "volume_usd": v})

    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
    for c in ["price_usd", "market_cap_usd", "volume_usd"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["coin_id"] = COIN_ID

    published = publish_dataframe_from_dir(producer_dir, df=df, catalog=CATALOG)
    print(json.dumps(published.metadata(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
