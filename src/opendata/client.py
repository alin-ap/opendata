from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from .errors import NotFoundError
from .ids import data_key, latest_key, validate_dataset_id, validate_version
from .publish import publish_dataframe
from .storage import storage_from_env
from .storage.base import StorageBackend
from .versioning import default_version


def _default_cache_dir() -> Path:
    env = os.environ.get("OPENDATA_CACHE_DIR")
    if env:
        return Path(env)
    return Path.home() / ".cache" / "opendata"


def _cache_path_for_parquet(dataset_id: str, version: str, cache_dir: Path) -> Path:
    # Mirror the on-bucket layout under the cache directory.
    return cache_dir / data_key(dataset_id, version)


def _read_latest_pointer(storage: StorageBackend, dataset_id: str) -> dict[str, Any]:
    lk = latest_key(dataset_id)
    raw = storage.get_bytes(lk)
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise NotFoundError(f"invalid latest pointer for {dataset_id!r}")
    return data


def resolve_version(storage: StorageBackend, dataset_id: str, version: Optional[str]) -> str:
    """Resolve version for dataset_id.

    If version is None, reads `<dataset>/latest.json`.
    """

    validate_dataset_id(dataset_id)
    if version is not None:
        return validate_version(version)

    latest = _read_latest_pointer(storage, dataset_id)
    v = latest.get("version")
    if not isinstance(v, str):
        raise NotFoundError(f"latest.json missing 'version' for {dataset_id!r}")
    return validate_version(v)


def load(
    dataset_id: str,
    *,
    version: Optional[str] = None,
    storage: Optional[StorageBackend] = None,
    cache_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """Load a dataset into a pandas DataFrame."""

    storage = storage or storage_from_env()
    cache_dir = cache_dir or _default_cache_dir()

    v = resolve_version(storage, dataset_id, version)
    cache_path = _cache_path_for_parquet(dataset_id, v, cache_dir)

    if not cache_path.exists():
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        storage.download_file(data_key(dataset_id, v), cache_path)

    return pd.read_parquet(cache_path)


def load_parquet_path(
    dataset_id: str,
    *,
    version: Optional[str] = None,
    storage: Optional[StorageBackend] = None,
    cache_dir: Optional[Path] = None,
) -> Path:
    """Download (if needed) and return the local parquet path."""

    storage = storage or storage_from_env()
    cache_dir = cache_dir or _default_cache_dir()

    v = resolve_version(storage, dataset_id, version)
    cache_path = _cache_path_for_parquet(dataset_id, v, cache_dir)

    if not cache_path.exists():
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        storage.download_file(data_key(dataset_id, v), cache_path)

    return cache_path


def push(
    dataset_id: str,
    df: pd.DataFrame,
    *,
    version: Optional[str] = None,
    storage: Optional[StorageBackend] = None,
) -> None:
    """Publish a pandas DataFrame to storage as Parquet."""

    storage = storage or storage_from_env()
    v = validate_version(version) if version is not None else default_version()

    validate_dataset_id(dataset_id)

    publish_dataframe(storage, dataset_id=dataset_id, df=df, version=v)
