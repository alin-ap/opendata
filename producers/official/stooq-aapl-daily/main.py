from __future__ import annotations

from io import StringIO
from pathlib import Path

import pandas as pd
import requests

URL = "https://stooq.com/q/d/l/?s=aapl.us&i=d"
SYMBOL = "AAPL.US"


def main() -> None:
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

    out_dir = Path(__file__).resolve().parent / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / "data.parquet", index=False)


if __name__ == "__main__":
    main()
