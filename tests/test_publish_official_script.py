from __future__ import annotations

import json
import sys
from pathlib import Path


def _write_meta(path: Path, dataset_id: str) -> None:
    path.write_text(
        f"""meta_version: 1
id: {dataset_id}
title: Test
description: Test
license: MIT
source: https://example.com
repo: https://github.com/example/repo
""",
        encoding="utf-8",
    )


def test_publish_official_script_ignore_failures(tmp_path: Path, monkeypatch) -> None:
    # Local storage for publishing.
    bucket = tmp_path / "bucket"
    monkeypatch.setenv("OPENDATA_STORAGE", "local")
    monkeypatch.setenv("OPENDATA_LOCAL_STORAGE_DIR", str(bucket))

    # Two producers: one succeeds, one fails.
    root = tmp_path / "producers"
    ok = root / "ok"
    bad = root / "bad"
    ok.mkdir(parents=True)
    bad.mkdir(parents=True)

    _write_meta(ok / "opendata.yaml", "official/ok-dataset")
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

    _write_meta(bad / "opendata.yaml", "official/bad-dataset")
    (bad / "main.py").write_text(
        """from __future__ import annotations

raise SystemExit(1)
""",
        encoding="utf-8",
    )

    # Import after env set.
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    from scripts.publish_official_local import main

    rc = main(
        [
            "--root",
            str(root),
            "--version",
            "2026-01-24",
            "--ignore-failures",
        ]
    )
    assert rc == 0

    # The ok dataset should be published.
    latest_path = bucket / "datasets" / "official" / "ok-dataset" / "latest.json"
    assert latest_path.exists()
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest["version"] == "2026-01-24"

    index = json.loads((bucket / "index.json").read_text(encoding="utf-8"))
    assert len(index["datasets"]) == 2
    ids = [d["id"] for d in index["datasets"]]
    assert "official/ok-dataset" in ids
    assert "official/bad-dataset" in ids
