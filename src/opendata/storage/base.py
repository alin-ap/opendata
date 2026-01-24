from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class StorageBackend(ABC):
    """Abstract storage backend.

    Storage is addressed by object keys like `datasets/<namespace>/<name>/...`.
    """

    @abstractmethod
    def exists(self, key: str) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def get_bytes(self, key: str) -> bytes:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def put_bytes(
        self, key: str, data: bytes, *, content_type: Optional[str] = None
    ) -> None:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def download_file(self, key: str, dest_path: Path) -> None:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def upload_file(
        self, key: str, src_path: Path, *, content_type: Optional[str] = None
    ) -> None:  # pragma: no cover
        raise NotImplementedError
