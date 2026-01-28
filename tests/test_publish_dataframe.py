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

    catalog = {
        "id": dataset_id,
        "title": "Example",
        "description": "Example dataset",
        "license": "MIT",
        "repo": "https://github.com/example/repo",
        "source": {"provider": "example", "homepage": "https://example.com"},
        "topics": ["example"],
        "owners": ["example"],
        "frequency": "adhoc",
    }

    published = publish_dataframe(
        storage,
        dataset_id=dataset_id,
        df=df,
        preview_rows=2,
        catalog=catalog,
    )

    assert published.data_key == data_key(dataset_id)

    meta = json.loads(storage.get_bytes(published.metadata_key))
    assert meta["dataset_id"] == dataset_id
    assert meta["row_count"] == 3
    assert meta["data_size_bytes"] > 0
    assert meta["title"] == "Example"

    preview = meta.get("preview")
    assert preview is not None
    assert len(preview["rows"]) == 2
