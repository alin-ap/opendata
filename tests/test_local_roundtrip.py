from __future__ import annotations

from pathlib import Path

import pandas as pd

from opendata.client import load
from opendata.publish import publish_dataframe, publish_parquet_file
from opendata.storage.memory import MemoryStorage


def test_publish_dataframe_and_load_roundtrip() -> None:
    storage = MemoryStorage()
    dataset_id = "getopendata/us-stock-daily"
    df_in = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    catalog = {
        "id": dataset_id,
        "title": "US Stock Daily",
        "description": "Daily OHLCV bars for US stocks.",
        "license": "MIT",
        "repo": "https://github.com/example/repo",
        "topics": ["stocks"],
        "owners": ["example"],
        "frequency": "daily",
    }
    publish_dataframe(storage, dataset_id=dataset_id, df=df_in, preview_rows=2, catalog=catalog)

    df_out = load(dataset_id, storage=storage)
    pd.testing.assert_frame_equal(df_in, df_out)


def test_publish_parquet_file_and_load_roundtrip(tmp_path: Path) -> None:
    storage = MemoryStorage()
    dataset_id = "getopendata/us-stock-daily"

    df_in = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    parquet_path = tmp_path / "in.parquet"
    df_in.to_parquet(parquet_path, index=False)

    catalog = {
        "id": dataset_id,
        "title": "US Stock Daily",
        "description": "Daily OHLCV bars for US stocks.",
        "license": "MIT",
        "repo": "https://github.com/example/repo",
        "topics": ["stocks"],
        "owners": ["example"],
        "frequency": "daily",
    }
    publish_parquet_file(
        storage, dataset_id=dataset_id, parquet_path=parquet_path, preview_rows=2, catalog=catalog
    )

    df_out = load(dataset_id, storage=storage)
    pd.testing.assert_frame_equal(df_in, df_out)
