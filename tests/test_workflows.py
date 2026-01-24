from __future__ import annotations

from pathlib import Path


def test_publish_official_workflow_exists_and_has_schedule() -> None:
    root = Path(__file__).resolve().parents[1]
    wf = root / ".github" / "workflows" / "publish_official.yml"
    assert wf.exists()

    text = wf.read_text(encoding="utf-8")
    assert "schedule" in text
    assert "workflow_dispatch" in text
    assert "scripts/publish_official_local.py" in text
    assert "OPENDATA_R2_ENDPOINT_URL" in text
    assert "OPENDATA_R2_BUCKET" in text
    assert "OPENDATA_R2_ACCESS_KEY_ID" in text
    assert "OPENDATA_R2_SECRET_ACCESS_KEY" in text


def test_pages_workflow_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    wf = root / ".github" / "workflows" / "pages.yml"
    assert wf.exists()

    text = wf.read_text(encoding="utf-8")
    assert "deploy-pages" in text
    assert "upload-pages-artifact" in text
