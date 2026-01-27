from __future__ import annotations

from pathlib import Path


def test_portal_files_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "portal" / "index.html").exists()
    assert (root / "portal" / "app.js").exists()
    assert (root / "portal" / "styles.css").exists()


def test_portal_html_references_assets() -> None:
    root = Path(__file__).resolve().parents[1]
    html = (root / "portal" / "index.html").read_text(encoding="utf-8")
    assert "app.js" in html
    assert "styles.css" in html
    assert "config.js" in html
