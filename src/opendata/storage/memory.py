from __future__ import annotations

from typing import Optional

from ..errors import NotFoundError
from .base import StorageBackend


class MemoryStorage(StorageBackend):
    """In-memory storage backend.

    This backend is primarily intended for tests and local experimentation.
    """

    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    def exists(self, key: str) -> bool:
        return key in self._objects

    def get_bytes(self, key: str) -> bytes:
        try:
            return self._objects[key]
        except KeyError as e:
            raise NotFoundError(f"not found: {key}") from e

    def put_bytes(self, key: str, data: bytes, *, content_type: Optional[str] = None) -> None:
        _ = content_type
        self._objects[key] = bytes(data)


_GLOBAL: Optional[MemoryStorage] = None


def get_memory_storage() -> MemoryStorage:
    """Return the process-global MemoryStorage instance."""

    global _GLOBAL
    if _GLOBAL is None:
        _GLOBAL = MemoryStorage()
    return _GLOBAL


def reset_memory_storage() -> MemoryStorage:
    """Reset and return a fresh process-global MemoryStorage instance."""

    global _GLOBAL
    _GLOBAL = MemoryStorage()
    return _GLOBAL
