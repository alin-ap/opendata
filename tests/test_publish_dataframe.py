from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from opendata.ids import data_key, latest_key
from opendata.publish import publish_dataframe
from opendata.storage.local import LocalStorage


def test_publish_dataframe_writes_objects(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    dataset_id = "official/example-df"
    version = "2026-01-24"

    df = pd.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})

    published = publish_dataframe(
        storage,
        dataset_id=dataset_id,
        df=df,
        version=version,
        preview_rows=2,
    )

    assert published.data_key == data_key(dataset_id, version)

    latest = json.loads(storage.get_bytes(latest_key(dataset_id)))
    assert latest["version"] == version
    assert latest["row_count"] == 3
    assert latest["data_size_bytes"] > 0
    assert latest["preview_key"].endswith("/preview.json")

    preview = json.loads(storage.get_bytes(latest["preview_key"]))
    assert len(preview["rows"]) == 2
