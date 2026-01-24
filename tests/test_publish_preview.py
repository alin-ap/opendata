from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from opendata.ids import latest_key
from opendata.publish import publish_parquet_file
from opendata.storage.local import LocalStorage


def test_publish_writes_preview_and_latest_fields(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    dataset_id = "official/stooq-aapl-daily"
    version = "2026-01-24"

    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    parquet_path = tmp_path / "data.parquet"
    df.to_parquet(parquet_path, index=False)

    published = publish_parquet_file(
        storage,
        dataset_id=dataset_id,
        parquet_path=parquet_path,
        version=version,
        preview_rows=2,
    )

    assert published.preview_key.endswith("/preview.json")
    preview = json.loads(storage.get_bytes(published.preview_key))
    assert preview["dataset_id"] == dataset_id
    assert preview["version"] == version
    assert len(preview["rows"]) == 2

    latest = json.loads(storage.get_bytes(latest_key(dataset_id)))
    assert latest["preview_key"] == published.preview_key
    assert latest["data_size_bytes"] == parquet_path.stat().st_size
