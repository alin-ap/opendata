from __future__ import annotations

from pathlib import Path

from opendata.portal_publish import publish_portal_assets
from opendata.storage.local import LocalStorage


def test_publish_portal_assets_writes_expected_files(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    repo_root = Path(__file__).resolve().parents[1]
    portal_dir = repo_root / "portal"

    publish_portal_assets(storage, portal_dir=portal_dir)

    assert (tmp_path / "portal" / "index.html").exists()
    assert (tmp_path / "portal" / "app.js").exists()
    assert (tmp_path / "portal" / "styles.css").exists()
