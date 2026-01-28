from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from opendata.ids import readme_key
from opendata.producer import publish_dataframe_from_dir
from opendata.storage.memory import MemoryStorage


def test_publish_dataframe_from_dir_uploads_readme(tmp_path: Path) -> None:
    producer_dir = tmp_path / "producer"
    producer_dir.mkdir(parents=True)

    catalog = {
        "id": "getopendata/example-producer",
        "title": "Example",
        "description": "Example dataset",
        "license": "MIT",
        "repo": "https://github.com/example/repo",
        "source": {"provider": "example", "homepage": "https://example.com"},
    }
    (producer_dir / "README.md").write_text("# Hello\n", encoding="utf-8")

    storage = MemoryStorage()
    df = pd.DataFrame({"a": [1, 2, 3]})

    published = publish_dataframe_from_dir(
        producer_dir,
        df=df,
        catalog=catalog,
        storage=storage,
        preview_rows=2,
    )

    assert storage.exists(published.data_key)
    assert storage.exists(published.metadata_key)

    meta = json.loads(storage.get_bytes(published.metadata_key))
    assert meta.get("preview") is not None
    assert meta.get("title") == "Example"
    assert (
        storage.get_bytes(readme_key("getopendata/example-producer"))
        .decode("utf-8")
        .startswith("# Hello")
    )
