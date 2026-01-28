from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import requests

from opendata.producer import publish_dataframe_from_dir


CATALOG = {
  "id": "getopendata/owid-covid-global-daily",
  "title": "OWID COVID Global Daily",
  "description": "Daily COVID metrics by location from Our World in Data (selected columns).",
  "license": "CC-BY-4.0",
  "repo": "https://github.com/getopendata/getopendata",
  "topics": [
    "health",
    "covid"
  ],
  "owners": [
    "alin"
  ],
  "frequency": "daily",
  "source": {
    "provider": "owid",
    "homepage": "https://ourworldindata.org/",
    "dataset": "https://github.com/owid/covid-19-data/tree/master/public/data"
  },
  "geo": {
    "scope": "global"
  }
}

URL = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv"

USECOLS = [
    "iso_code",
    "continent",
    "location",
    "date",
    "total_cases",
    "new_cases",
    "total_deaths",
    "new_deaths",
    "population",
]


def _download_csv(tmp_path: Path) -> None:
    with requests.get(URL, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with tmp_path.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)


def main() -> None:
    producer_dir = Path(__file__).resolve().parent

    with tempfile.TemporaryDirectory() as td:
        csv_path = Path(td) / "owid.csv"
        _download_csv(csv_path)

        df = pd.read_csv(csv_path, usecols=USECOLS, parse_dates=["date"])
        for c in ["total_cases", "new_cases", "total_deaths", "new_deaths", "population"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        published = publish_dataframe_from_dir(producer_dir, df=df, catalog=CATALOG)
        print(json.dumps(published.metadata(), indent=2, sort_keys=True))

    # Avoid leaving large intermediates.
    os.sync()


if __name__ == "__main__":
    main()
