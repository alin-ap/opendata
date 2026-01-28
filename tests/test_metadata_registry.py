from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from opendata.metadata import DatasetCatalog
from opendata.publish import publish_parquet_file
from opendata.registry import Registry
from opendata.storage.memory import MemoryStorage


def test_catalog_from_dict() -> None:
    catalog = DatasetCatalog.from_dict(
        {
            "id": "getopendata/us-stock-daily",
            "title": "US Stock Daily",
            "description": "Daily OHLCV bars for US stocks.",
            "license": "MIT",
            "repo": "https://github.com/example/repo",
            "source": {"provider": "stooq", "homepage": "https://stooq.com/"},
            "topics": ["stocks", "us"],
            "owners": ["example"],
            "frequency": "daily",
        }
    )

    assert catalog.id == "getopendata/us-stock-daily"
    assert catalog.title == "US Stock Daily"
    assert "stocks" in catalog.topics


def test_registry_register_and_refresh(tmp_path: Path) -> None:
    storage = MemoryStorage()
    reg = Registry(storage)
    dataset_id = "getopendata/us-stock-daily"
    catalog = {
        "id": dataset_id,
        "title": "US Stock Daily",
        "description": "Daily OHLCV bars for US stocks.",
        "license": "MIT",
        "repo": "https://github.com/example/repo",
        "source": {"provider": "stooq", "homepage": "https://stooq.com/"},
        "topics": ["stocks", "us"],
        "owners": ["example"],
        "frequency": "daily",
    }

    df = pd.DataFrame({"a": [1, 2, 3]})
    parquet_path = tmp_path / "data.parquet"
    df.to_parquet(parquet_path, index=False)
    publish_parquet_file(
        storage,
        dataset_id=dataset_id,
        parquet_path=parquet_path,
        preview_rows=2,
        catalog=catalog,
    )

    reg.refresh_metadata(dataset_id)
    index2 = json.loads(storage.get_bytes("index.json"))
    entry = index2["datasets"][0]
    assert entry["id"] == dataset_id
    assert entry["title"] == "US Stock Daily"
    assert entry["row_count"] == 3
