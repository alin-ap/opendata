from __future__ import annotations

import json

import pandas as pd

from opendata.ids import data_key
from opendata.publish import publish_dataframe
from opendata.storage.memory import MemoryStorage


def test_publish_dataframe_writes_objects() -> None:
    storage = MemoryStorage()
    dataset_id = "getopendata/example-df"

    df = pd.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})

    published = publish_dataframe(
        storage,
        dataset_id=dataset_id,
        df=df,
        preview_rows=2,
    )

    assert published.data_key == data_key(dataset_id)

    meta = json.loads(storage.get_bytes(published.metadata_key))
    assert meta["dataset_id"] == dataset_id
    assert meta["row_count"] == 3
    assert meta["data_size_bytes"] > 0
    assert meta["data_key"] == published.data_key
    assert meta["metadata_key"] == published.metadata_key

    preview = meta.get("preview")
    assert preview is not None
    assert len(preview["rows"]) == 2
