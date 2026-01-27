from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from opendata.publish import publish_dataframe
from opendata.registry import Registry
from opendata.storage.memory import MemoryStorage


def test_registry_build_from_producers(tmp_path: Path) -> None:
    storage = MemoryStorage()
    reg = Registry(storage)

    producers = tmp_path / "producers"
    (producers / "a").mkdir(parents=True)
    (producers / "b").mkdir(parents=True)

    (producers / "a" / "opendata.yaml").write_text(
        """id: alice/a
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
        """id: alice/b
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
        dataset_id="alice/a",
        df=pd.DataFrame({"x": [1, 2, 3]}),
        preview_rows=1,
    )

    reg.build_from_producer_root(producers)
    idx = json.loads(storage.get_bytes("index.json"))
    assert len(idx["datasets"]) == 2

    a = [d for d in idx["datasets"] if d["id"] == "alice/a"][0]
    b = [d for d in idx["datasets"] if d["id"] == "alice/b"][0]

    assert "metadata_key" in a
    assert "metadata_key" not in b
