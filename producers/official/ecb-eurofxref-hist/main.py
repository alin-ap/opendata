from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from opendata.producer import publish_dataframe_from_dir

URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.csv"


def main() -> None:
    producer_dir = Path(__file__).resolve().parent

    resp = requests.get(URL, timeout=60)
    resp.raise_for_status()

    wide = pd.read_csv(StringIO(resp.text))
    wide.columns = [c.strip() for c in wide.columns]

    # The first column is "Date".
    wide = wide.rename(columns={"Date": "date"})
    wide["date"] = pd.to_datetime(wide["date"], utc=True)

    long = wide.melt(id_vars=["date"], var_name="currency", value_name="rate")
    long["currency"] = long["currency"].astype(str)
    long["rate"] = pd.to_numeric(long["rate"], errors="coerce")
    long = long.dropna(subset=["rate"]).reset_index(drop=True)

    published = publish_dataframe_from_dir(producer_dir, df=long)
    print(json.dumps(published.latest_pointer(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
