from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from opendata.producer import publish_dataframe_from_dir

SERIES_ID = "FEDFUNDS"
URL = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES_ID}"


def main() -> None:
    producer_dir = Path(__file__).resolve().parent

    resp = requests.get(URL, timeout=60)
    resp.raise_for_status()

    df = pd.read_csv(StringIO(resp.text))
    df.columns = [c.strip().lower() for c in df.columns]
    date_col = "observation_date" if "observation_date" in df.columns else "date"
    df = df.rename(columns={date_col: "date", SERIES_ID.lower(): "value"})

    df["date"] = pd.to_datetime(df["date"], utc=True)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["series_id"] = SERIES_ID

    published = publish_dataframe_from_dir(producer_dir, df=df)
    print(json.dumps(published.latest_pointer(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
