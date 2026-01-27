from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from opendata.metadata import load_metadata
from opendata.publish import publish_parquet_file
from opendata.registry import Registry
from opendata.storage.local import LocalStorage


def test_load_metadata(tmp_path: Path) -> None:
    meta_path = tmp_path / "opendata.yaml"
    meta_path.write_text(
        """id: official/us-stock-daily
title: US Stock Daily
description: Daily OHLCV bars for US stocks.
license: MIT
repo: https://github.com/example/repo
source:
  provider: stooq
  homepage: https://stooq.com/
topics: [stocks, us]
owners: [example]
""",
        encoding="utf-8",
    )

    meta = load_metadata(meta_path)
    assert meta.id == "official/us-stock-daily"
    assert meta.meta_version == 2
    assert meta.title == "US Stock Daily"
    assert "stocks" in meta.topics


def test_registry_register_and_refresh(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path / "bucket")
    reg = Registry(storage)

    meta_path = tmp_path / "opendata.yaml"
    meta_path.write_text(
        """id: official/us-stock-daily
title: US Stock Daily
description: Daily OHLCV bars for US stocks.
license: MIT
repo: https://github.com/example/repo
source:
  provider: stooq
  homepage: https://stooq.com/
""",
        encoding="utf-8",
    )

    meta = reg.register_from_file(meta_path)
    index = json.loads(storage.get_bytes("index.json"))
    assert index["datasets"][0]["id"] == meta.id

    df = pd.DataFrame({"a": [1, 2, 3]})
    parquet_path = tmp_path / "data.parquet"
    df.to_parquet(parquet_path, index=False)
    published = publish_parquet_file(
        storage,
        dataset_id=meta.id,
        parquet_path=parquet_path,
        preview_rows=2,
    )

    reg.refresh_metadata(meta.id)
    index2 = json.loads(storage.get_bytes("index.json"))
    entry = index2["datasets"][0]
    assert entry["id"] == meta.id
    assert entry["row_count"] == 3
    assert entry["preview_key"] == published.preview_key
    assert entry["data_key"] == published.data_key
    assert entry["metadata_key"] == published.metadata_key
