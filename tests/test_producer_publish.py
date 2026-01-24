from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from opendata.ids import latest_key, readme_key
from opendata.producer import publish_dataframe_from_dir
from opendata.storage.local import LocalStorage


def test_publish_dataframe_from_dir_uploads_readme(tmp_path: Path) -> None:
    producer_dir = tmp_path / "producer"
    producer_dir.mkdir(parents=True)

    (producer_dir / "opendata.yaml").write_text(
        """meta_version: 1
id: official/example-producer
title: Example
description: Example dataset
license: MIT
source: https://example.com
repo: https://github.com/example/repo
""",
        encoding="utf-8",
    )
    (producer_dir / "README.md").write_text("# Hello\n", encoding="utf-8")

    storage = LocalStorage(tmp_path / "bucket")
    df = pd.DataFrame({"a": [1, 2, 3]})

    published = publish_dataframe_from_dir(
        producer_dir,
        df=df,
        storage=storage,
        version="2026-01-24",
        preview_rows=2,
    )

    latest = json.loads(storage.get_bytes(latest_key("official/example-producer")))
    assert latest["version"] == "2026-01-24"
    assert latest["preview_key"] == published.preview_key

    assert (
        storage.get_bytes(readme_key("official/example-producer"))
        .decode("utf-8")
        .startswith("# Hello")
    )
