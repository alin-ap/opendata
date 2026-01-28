from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from opendata.publish import publish_dataframe
from opendata.registry import Registry
from opendata.storage.memory import MemoryStorage


def test_registry_refresh_creates_entries(tmp_path: Path) -> None:
    storage = MemoryStorage()
    reg = Registry(storage)

    publish_dataframe(
        storage,
        dataset_id="alice/a",
        df=pd.DataFrame({"x": [1, 2, 3]}),
        preview_rows=1,
        catalog={
            "id": "alice/a",
            "title": "A",
            "description": "A",
            "license": "MIT",
            "repo": "https://github.com/example/repo",
            "source": {"provider": "example", "homepage": "https://example.com"},
        },
    )

    publish_dataframe(
        storage,
        dataset_id="alice/b",
        df=pd.DataFrame({"y": [4, 5]}),
        preview_rows=1,
        catalog={
            "id": "alice/b",
            "title": "B",
            "description": "B",
            "license": "MIT",
            "repo": "https://github.com/example/repo",
            "source": {"provider": "example", "homepage": "https://example.com"},
        },
    )

    reg.refresh_metadata("alice/a")
    reg.refresh_metadata("alice/b")

    idx = json.loads(storage.get_bytes("index.json"))
    assert len(idx["datasets"]) == 2

    a = [d for d in idx["datasets"] if d["id"] == "alice/a"][0]
    b = [d for d in idx["datasets"] if d["id"] == "alice/b"][0]

    assert a["title"] == "A"
    assert b["title"] == "B"
