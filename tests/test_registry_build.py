from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from opendata.publish import publish_dataframe
from opendata.registry import Registry
from opendata.storage.local import LocalStorage


def test_registry_build_from_producers(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path / "bucket")
    reg = Registry(storage)

    producers = tmp_path / "producers"
    (producers / "a").mkdir(parents=True)
    (producers / "b").mkdir(parents=True)

    (producers / "a" / "opendata.yaml").write_text(
        """meta_version: 2
id: official/a
title: A
description: A
license: MIT
repo: https://github.com/example/repo
source:
  provider: example
  homepage: https://example.com
""",
        encoding="utf-8",
    )

    (producers / "b" / "opendata.yaml").write_text(
        """meta_version: 2
id: official/b
title: B
description: B
license: MIT
repo: https://github.com/example/repo
source:
  provider: example
  homepage: https://example.com
""",
        encoding="utf-8",
    )

    # Only publish one dataset.
    publish_dataframe(
        storage,
        dataset_id="official/a",
        df=pd.DataFrame({"x": [1, 2, 3]}),
        version="2026-01-24",
        preview_rows=1,
    )

    reg.build_from_producer_root(producers)
    idx = json.loads(storage.get_bytes("index.json"))
    assert idx["meta_version"] == 1
    assert len(idx["datasets"]) == 2

    a = [d for d in idx["datasets"] if d["id"] == "official/a"][0]
    b = [d for d in idx["datasets"] if d["id"] == "official/b"][0]

    assert a["version"] == "2026-01-24"
    assert "preview_key" in a
    assert "version" not in b
