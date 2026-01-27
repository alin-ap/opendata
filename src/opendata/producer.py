from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa

from .metadata import DatasetMetadata, load_metadata
from .publish import PublishedDataset, publish_dataframe, publish_table, upload_readme
from .storage import storage_from_env
from .storage.base import StorageBackend


def producer_metadata_path(producer_dir: Path) -> Path:
    return producer_dir / "opendata.yaml"


def producer_readme_path(producer_dir: Path) -> Path:
    return producer_dir / "README.md"


def load_producer_metadata(producer_dir: Path) -> DatasetMetadata:
    return load_metadata(producer_metadata_path(producer_dir))


def resolve_preview_rows(preview_rows: Optional[int] = None) -> int:
    if preview_rows is not None:
        return int(preview_rows)
    env = os.environ.get("OPENDATA_PREVIEW_ROWS")
    if env:
        try:
            return int(env)
        except ValueError:
            return 100
    return 100


def publish_dataframe_from_dir(
    producer_dir: Path,
    *,
    df: pd.DataFrame,
    preview_rows: Optional[int] = None,
    storage: Optional[StorageBackend] = None,
) -> PublishedDataset:
    """Publish a DataFrame for the dataset described in `producer_dir/opendata.yaml`."""

    meta = load_producer_metadata(producer_dir)
    pr = resolve_preview_rows(preview_rows)
    storage = storage or storage_from_env()

    published = publish_dataframe(
        storage,
        dataset_id=meta.id,
        df=df,
        preview_rows=pr,
    )

    readme = producer_readme_path(producer_dir)
    if readme.exists():
        upload_readme(storage, dataset_id=meta.id, readme_path=readme)

    return published


def publish_table_from_dir(
    producer_dir: Path,
    *,
    table: pa.Table,
    preview_rows: Optional[int] = None,
    storage: Optional[StorageBackend] = None,
) -> PublishedDataset:
    meta = load_producer_metadata(producer_dir)
    pr = resolve_preview_rows(preview_rows)
    storage = storage or storage_from_env()

    published = publish_table(
        storage,
        dataset_id=meta.id,
        table=table,
        preview_rows=pr,
    )

    readme = producer_readme_path(producer_dir)
    if readme.exists():
        upload_readme(storage, dataset_id=meta.id, readme_path=readme)

    return published
