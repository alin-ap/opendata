from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd
import requests

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
    out_dir = Path(__file__).resolve().parent / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        csv_path = Path(td) / "owid.csv"
        _download_csv(csv_path)

        df = pd.read_csv(csv_path, usecols=USECOLS, parse_dates=["date"])
        for c in ["total_cases", "new_cases", "total_deaths", "new_deaths", "population"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df.to_parquet(out_dir / "data.parquet", index=False)

    # Avoid leaving large intermediates.
    os.sync()


if __name__ == "__main__":
    main()
