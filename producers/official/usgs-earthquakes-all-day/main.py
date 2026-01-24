from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from opendata.producer import publish_dataframe_from_dir

URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"


def _get_json(url: str) -> dict[str, Any]:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, dict):
        raise ValueError("unexpected response")
    return data


def main() -> None:
    producer_dir = Path(__file__).resolve().parent

    data = _get_json(URL)
    feats = data.get("features") or []

    rows: list[dict[str, Any]] = []
    for f in feats:
        if not isinstance(f, dict):
            continue
        props = f.get("properties") or {}
        geom = f.get("geometry") or {}
        coords = geom.get("coordinates") or []

        lon = coords[0] if isinstance(coords, list) and len(coords) >= 1 else None
        lat = coords[1] if isinstance(coords, list) and len(coords) >= 2 else None
        depth = coords[2] if isinstance(coords, list) and len(coords) >= 3 else None

        rows.append(
            {
                "event_id": f.get("id"),
                "time": props.get("time"),
                "updated_at": props.get("updated"),
                "mag": props.get("mag"),
                "place": props.get("place"),
                "tsunami": props.get("tsunami"),
                "url": props.get("url"),
                "longitude": lon,
                "latitude": lat,
                "depth_km": depth,
            }
        )

    df = pd.DataFrame(rows)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
    if "updated_at" in df.columns:
        df["updated_at"] = pd.to_datetime(df["updated_at"], unit="ms", utc=True)
    for c in ["mag", "longitude", "latitude", "depth_km"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "tsunami" in df.columns:
        df["tsunami"] = pd.to_numeric(df["tsunami"], errors="coerce").astype("Int64")

    published = publish_dataframe_from_dir(producer_dir, df=df)
    print(json.dumps(published.latest_pointer(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
