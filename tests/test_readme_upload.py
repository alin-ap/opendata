from __future__ import annotations

from pathlib import Path

from opendata.ids import readme_key
from opendata.publish import upload_readme
from opendata.storage.local import LocalStorage


def test_upload_readme_writes_expected_key(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    dataset_id = "official/stooq-aapl-daily"

    src = tmp_path / "README.md"
    src.write_text("# Hello\n\nworld\n", encoding="utf-8")

    key = upload_readme(storage, dataset_id=dataset_id, readme_path=src)
    assert key == readme_key(dataset_id)
    assert storage.get_bytes(key).decode("utf-8").startswith("# Hello")
