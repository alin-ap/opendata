from __future__ import annotations

from pathlib import Path

from opendata.portal_publish import publish_portal_assets
from opendata.storage.memory import MemoryStorage


def test_publish_portal_assets_writes_expected_files() -> None:
    storage = MemoryStorage()
    repo_root = Path(__file__).resolve().parents[1]
    portal_dir = repo_root / "portal"

    publish_portal_assets(storage, portal_dir=portal_dir)

    assert storage.exists("portal/index.html")
    assert storage.exists("portal/app.js")
    assert storage.exists("portal/styles.css")
