from __future__ import annotations

import shutil
from pathlib import Path, PurePosixPath
from typing import Optional

from ..errors import NotFoundError, StorageError
from .base import StorageBackend


class LocalStorage(StorageBackend):
    """Local filesystem storage backend.

    Useful for development and unit tests.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def _path_for_key(self, key: str) -> Path:
        p = PurePosixPath(key)
        if p.is_absolute() or ".." in p.parts:
            raise StorageError(f"invalid storage key: {key!r}")

        full = (self._base_dir / Path(*p.parts)).resolve()
        base = self._base_dir.resolve()
        if base != full and base not in full.parents:
            raise StorageError(f"storage key escapes base_dir: {key!r}")
        return full

    def exists(self, key: str) -> bool:
        return self._path_for_key(key).exists()

    def get_bytes(self, key: str) -> bytes:
        path = self._path_for_key(key)
        if not path.exists():
            raise NotFoundError(f"not found: {key}")
        return path.read_bytes()

    def put_bytes(self, key: str, data: bytes, *, content_type: Optional[str] = None) -> None:
        _ = content_type
        path = self._path_for_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def download_file(self, key: str, dest_path: Path) -> None:
        src = self._path_for_key(key)
        if not src.exists():
            raise NotFoundError(f"not found: {key}")
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest_path)

    def upload_file(self, key: str, src_path: Path, *, content_type: Optional[str] = None) -> None:
        _ = content_type
        dest = self._path_for_key(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_path, dest)
