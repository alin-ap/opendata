from __future__ import annotations

import os
from pathlib import Path

from ..env import load_dotenv
from ..errors import StorageError
from .base import StorageBackend
from .local import LocalStorage


def storage_from_env() -> StorageBackend:
    """Create a storage backend from environment variables.

    - OPENDATA_STORAGE: local|r2|http (default: local)
    - OPENDATA_LOCAL_STORAGE_DIR: base directory for local storage (default: .opendata/storage)
    - OPENDATA_HTTP_BASE_URL: base URL for HttpStorage (e.g. https://<bucket>.r2.dev/)
    - OPENDATA_INDEX_URL: if set and OPENDATA_STORAGE is unset, implies OPENDATA_STORAGE=http
      and derives the base URL from the index URL.
    """

    # Convenience for local development: allow `.env` to define OPENDATA_* variables.
    load_dotenv()

    kind_raw = os.environ.get("OPENDATA_STORAGE")
    index_url = os.environ.get("OPENDATA_INDEX_URL", "").strip()

    if not kind_raw and index_url:
        from .http import HttpStorage

        base_url = index_url.rsplit("/", 1)[0] + "/"
        return HttpStorage(base_url=base_url)

    kind = (kind_raw or "local").strip().lower()
    if kind in {"local", "file"}:
        base_dir = Path(os.environ.get("OPENDATA_LOCAL_STORAGE_DIR", ".opendata/storage"))
        return LocalStorage(base_dir)

    if kind in {"r2", "s3"}:
        from .r2 import R2Storage

        return R2Storage.from_env()

    if kind in {"http", "https", "public"}:
        from .http import HttpStorage

        base_url = os.environ.get("OPENDATA_HTTP_BASE_URL", "").strip()
        if not base_url:
            raise StorageError("missing OPENDATA_HTTP_BASE_URL")
        return HttpStorage(base_url=base_url)

    raise StorageError(f"unknown OPENDATA_STORAGE: {kind!r}")
