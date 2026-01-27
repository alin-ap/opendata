from __future__ import annotations

from typing import Optional

import requests

from ..errors import NotFoundError, StorageError
from .base import StorageBackend


class HttpStorage(StorageBackend):
    """Read-only storage backend backed by HTTP(S).

    This is designed for public buckets (e.g. Cloudflare R2 public read). It
    supports reading `index.json`, `metadata.json`, Parquet objects, etc.
    """

    def __init__(self, *, base_url: str, timeout_s: int = 60) -> None:
        base_url = base_url.strip()
        if not base_url:
            raise StorageError("base_url is required")
        if not base_url.endswith("/"):
            base_url += "/"
        self._base_url = base_url
        self._timeout_s = int(timeout_s)

    @property
    def base_url(self) -> str:
        return self._base_url

    def _url(self, key: str) -> str:
        # Keys are always POSIX-style relative paths like `datasets/x/y/...`.
        if key.startswith("/"):
            key = key[1:]
        return self._base_url + key

    def exists(self, key: str) -> bool:
        try:
            resp = requests.head(self._url(key), timeout=self._timeout_s)
            return resp.status_code == 200
        except Exception:
            return False

    def get_bytes(self, key: str) -> bytes:
        try:
            resp = requests.get(self._url(key), timeout=self._timeout_s)
            if resp.status_code == 404:
                raise NotFoundError(f"not found: {key}")
            resp.raise_for_status()
            return resp.content
        except NotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"failed to GET {key}") from e

    def put_bytes(self, key: str, data: bytes, *, content_type: Optional[str] = None) -> None:
        _ = (key, data, content_type)
        raise StorageError("HttpStorage is read-only")
