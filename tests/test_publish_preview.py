from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from opendata.publish import publish_parquet_file
from opendata.storage.memory import MemoryStorage


def test_publish_writes_preview_and_latest_fields(tmp_path: Path) -> None:
    storage = MemoryStorage()
    dataset_id = "getopendata/stooq-aapl-daily"

    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    parquet_path = tmp_path / "data.parquet"
    df.to_parquet(parquet_path, index=False)

    published = publish_parquet_file(
        storage,
        dataset_id=dataset_id,
        parquet_path=parquet_path,
        preview_rows=2,
    )

    meta = json.loads(storage.get_bytes(published.metadata_key))
    assert meta["dataset_id"] == dataset_id
    assert meta["data_size_bytes"] == parquet_path.stat().st_size
    preview = meta.get("preview")
    assert preview is not None
    assert len(preview["rows"]) == 2
