from __future__ import annotations

from pathlib import Path


def test_pages_workflow_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    wf = root / ".github" / "workflows" / "pages.yml"
    assert wf.exists()

    text = wf.read_text(encoding="utf-8")
    assert "deploy-pages" in text
    assert "upload-pages-artifact" in text
