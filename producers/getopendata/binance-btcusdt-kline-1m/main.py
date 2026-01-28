from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import requests

from opendata.producer import publish_dataframe_from_dir


CATALOG = {
  "id": "getopendata/binance-btcusdt-kline-1m",
  "title": "Binance BTCUSDT 1m Kline",
  "description": "One-minute OHLCV candles for BTCUSDT from Binance Spot API (rolling last 24h).",
  "license": "unknown",
  "repo": "https://github.com/getopendata/getopendata",
  "topics": [
    "crypto",
    "ohlcv",
    "btc",
    "usdt"
  ],
  "owners": [
    "alin"
  ],
  "frequency": "daily",
  "source": {
    "provider": "binance",
    "homepage": "https://www.binance.com/",
    "dataset": "https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data"
  }
}

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "BTCUSDT"
INTERVAL = "1m"
INTERVAL_MS = 60_000


def _utc_now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _floor_to_minute_ms(ts_ms: int) -> int:
    return (ts_ms // INTERVAL_MS) * INTERVAL_MS


def _get_json(url: str, *, params: dict[str, Any], timeout_s: int = 30) -> Any:
    last_exc: Optional[Exception] = None
    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, timeout=timeout_s)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if attempt == 2:
                raise
            time.sleep(0.5)
    raise RuntimeError("unreachable") from last_exc


def fetch_klines(*, start_ms: int, end_ms: int) -> list[list[Any]]:
    rows: list[list[Any]] = []
    cursor = start_ms

    while cursor < end_ms:
        params = {
            "symbol": SYMBOL,
            "interval": INTERVAL,
            "startTime": cursor,
            "endTime": end_ms,
            "limit": 1000,
        }
        chunk = _get_json(BINANCE_KLINES_URL, params=params)
        if not isinstance(chunk, list) or not chunk:
            break

        for item in chunk:
            if isinstance(item, list):
                rows.append(item)

        last_open_ms = rows[-1][0]
        if not isinstance(last_open_ms, int):
            break

        next_cursor = int(last_open_ms) + INTERVAL_MS
        if next_cursor <= cursor:
            break
        cursor = next_cursor

        # Be polite.
        if len(chunk) == 1000:
            time.sleep(0.2)

    return rows


def to_dataframe(rows: list[list[Any]]) -> pd.DataFrame:
    cols = [
        "open_time_ms",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time_ms",
        "quote_asset_volume",
        "num_trades",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
        "ignore",
    ]
    df = pd.DataFrame(rows)
    df.columns = cols

    df["open_time"] = pd.to_datetime(df.pop("open_time_ms"), unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(df.pop("close_time_ms"), unit="ms", utc=True)

    for c in [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_asset_volume",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
    ]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["num_trades"] = pd.to_numeric(df["num_trades"], errors="coerce")
    df["num_trades"] = df["num_trades"].astype("Int64")
    df["symbol"] = SYMBOL
    df["interval"] = INTERVAL
    return df


def main() -> None:
    producer_dir = Path(__file__).resolve().parent

    now_ms = _floor_to_minute_ms(_utc_now_ms())
    start_ms = now_ms - 24 * 60 * 60 * 1000

    rows = fetch_klines(start_ms=start_ms, end_ms=now_ms)
    df = to_dataframe(rows)

    published = publish_dataframe_from_dir(producer_dir, df=df, catalog=CATALOG)
    print(json.dumps(published.metadata(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
