from __future__ import annotations

from pathlib import Path
from typing import Optional

from .errors import StorageError
from .storage.base import StorageBackend


def _content_type_for_path(path: Path) -> Optional[str]:
    suf = path.suffix.lower()
    if suf == ".html":
        return "text/html; charset=utf-8"
    if suf == ".css":
        return "text/css; charset=utf-8"
    if suf == ".js":
        return "text/javascript; charset=utf-8"
    if suf == ".md":
        return "text/markdown; charset=utf-8"
    if suf == ".json":
        return "application/json"
    return None


def publish_portal_assets(
    storage: StorageBackend,
    *,
    portal_dir: Path,
    prefix: str = "portal/",
) -> None:
    """Upload static portal assets to storage.

    The portal is intentionally zero-build and can be served directly from a
    public bucket (e.g. Cloudflare R2).
    """

    if not portal_dir.exists():
        raise StorageError(f"portal_dir does not exist: {portal_dir}")

    prefix = prefix.lstrip("/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    files = [
        portal_dir / "index.html",
        portal_dir / "app.js",
        portal_dir / "styles.css",
        portal_dir / "README.md",
    ]

    for p in files:
        if not p.exists():
            continue
        key = prefix + p.name
        storage.put_bytes(key, p.read_bytes(), content_type=_content_type_for_path(p))
