from __future__ import annotations

import json
import sys
from pathlib import Path

from opendata.ids import data_key, metadata_key
from opendata.storage.memory import get_memory_storage, reset_memory_storage


def _write_meta(path: Path, dataset_id: str) -> None:
    path.write_text(
        f"""id: {dataset_id}
title: Test
description: Test
license: MIT
repo: https://github.com/example/repo
source:
  provider: test
  homepage: https://example.com
""",
        encoding="utf-8",
    )


def test_publish_producers_script_ignore_failures(tmp_path: Path, monkeypatch) -> None:
    reset_memory_storage()
    monkeypatch.setenv("OPENDATA_STORAGE", "memory")

    # Two producers: one succeeds, one fails.
    root = tmp_path / "producers"
    ok = root / "ok"
    bad = root / "bad"
    ok.mkdir(parents=True)
    bad.mkdir(parents=True)

    _write_meta(ok / "opendata.yaml", "alice/ok-dataset")
    (ok / "main.py").write_text(
        """from __future__ import annotations

from pathlib import Path

import pandas as pd

from opendata.producer import publish_dataframe_from_dir


def main() -> None:
    df = pd.DataFrame({"a": [1, 2, 3]})
    publish_dataframe_from_dir(Path(__file__).resolve().parent, df=df)


if __name__ == "__main__":
    main()
""",
        encoding="utf-8",
    )

    _write_meta(bad / "opendata.yaml", "alice/bad-dataset")
    (bad / "main.py").write_text(
        """from __future__ import annotations

raise SystemExit(1)
""",
        encoding="utf-8",
    )

    # Import after env set.
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    from scripts.publish_producers_local import main

    rc = main(["--root", str(root), "--ignore-failures"])
    assert rc == 0

    storage = get_memory_storage()
    assert storage.exists(data_key("alice/ok-dataset"))
    assert storage.exists(metadata_key("alice/ok-dataset"))

    index = json.loads(storage.get_bytes("index.json"))
    assert len(index["datasets"]) == 2
    ids = [d["id"] for d in index["datasets"]]
    assert "alice/ok-dataset" in ids
    assert "alice/bad-dataset" in ids
