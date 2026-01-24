from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

URL = "https://api.open-meteo.com/v1/forecast"
LATITUDE = 52.52
LONGITUDE = 13.41


def main() -> None:
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

    out_dir = Path(__file__).resolve().parent / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / "data.parquet", index=False)


if __name__ == "__main__":
    main()
