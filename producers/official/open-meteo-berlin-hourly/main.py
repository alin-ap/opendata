from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

from opendata.producer import publish_dataframe_from_dir

URL = "https://api.open-meteo.com/v1/forecast"
LATITUDE = 52.52
LONGITUDE = 13.41


def main() -> None:
    producer_dir = Path(__file__).resolve().parent

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "past_days": 7,
        "forecast_days": 0,
        "timezone": "UTC",
    }
    resp = requests.get(URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    hourly = data.get("hourly") or {}
    times = hourly.get("time") or []

    df = pd.DataFrame(
        {
            "time": pd.to_datetime(times, utc=True),
            "temperature_2m": hourly.get("temperature_2m"),
            "relative_humidity_2m": hourly.get("relative_humidity_2m"),
            "precipitation": hourly.get("precipitation"),
            "wind_speed_10m": hourly.get("wind_speed_10m"),
        }
    )
    df["latitude"] = float(LATITUDE)
    df["longitude"] = float(LONGITUDE)

    published = publish_dataframe_from_dir(producer_dir, df=df)
    print(json.dumps(published.latest_pointer(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
