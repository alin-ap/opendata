from __future__ import annotations

import os

from ..env import load_dotenv
from ..errors import StorageError
from .base import StorageBackend


def storage_from_env() -> StorageBackend:
    """Create a storage backend from environment variables.

    - OPENDATA_STORAGE: r2|http|memory
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

    if not kind_raw:
        base_url = os.environ.get("OPENDATA_HTTP_BASE_URL", "").strip()
        if base_url:
            from .http import HttpStorage

            return HttpStorage(base_url=base_url)
        raise StorageError(
            "missing storage config: set OPENDATA_INDEX_URL or OPENDATA_HTTP_BASE_URL, "
            "or set OPENDATA_STORAGE=r2"
        )

    kind = kind_raw.strip().lower()

    if kind in {"r2", "s3"}:
        from .r2 import R2Storage

        return R2Storage.from_env()

    if kind in {"memory", "mem"}:
        from .memory import get_memory_storage

        return get_memory_storage()

    if kind in {"local", "file"}:
        raise StorageError("local storage backend was removed; use OPENDATA_STORAGE=r2 or http")

    if kind in {"http", "https", "public"}:
        from .http import HttpStorage

        base_url = os.environ.get("OPENDATA_HTTP_BASE_URL", "").strip()
        if not base_url:
            raise StorageError("missing OPENDATA_HTTP_BASE_URL")
        return HttpStorage(base_url=base_url)

    raise StorageError(f"unknown OPENDATA_STORAGE: {kind!r}")
