from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from opendata.client import load, resolve_version
from opendata.ids import latest_key
from opendata.publish import publish_parquet_file
from opendata.storage.local import LocalStorage


def test_local_publish_and_load(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    dataset_id = "official/us-stock-daily"
    version = "2026-01-24"

    df_in = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    parquet_path = tmp_path / "in.parquet"
    df_in.to_parquet(parquet_path, index=False)

    publish_parquet_file(storage, dataset_id=dataset_id, parquet_path=parquet_path, version=version)

    df_out = load(dataset_id, version=version, storage=storage, cache_dir=tmp_path / "cache")
    pd.testing.assert_frame_equal(df_in, df_out)


def test_local_latest_pointer(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    dataset_id = "official/us-stock-daily"

    df = pd.DataFrame({"a": [1]})

    for version in ["2026-01-23", "2026-01-24"]:
        parquet_path = tmp_path / f"{version}.parquet"
        df.to_parquet(parquet_path, index=False)
        publish_parquet_file(
            storage, dataset_id=dataset_id, parquet_path=parquet_path, version=version
        )

    resolved = resolve_version(storage, dataset_id, version=None)
    assert resolved == "2026-01-24"

    latest = json.loads(storage.get_bytes(latest_key(dataset_id)))
    assert latest["version"] == "2026-01-24"
