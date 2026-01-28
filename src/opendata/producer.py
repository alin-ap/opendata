from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa

from .errors import ValidationError
from .metadata import CatalogInput, DatasetCatalog, coerce_catalog
from .publish import PublishedDataset, publish_dataframe, publish_table, upload_readme
from .storage import storage_from_env
from .storage.base import StorageBackend


def producer_readme_path(producer_dir: Path) -> Path:
    return producer_dir / "README.md"


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
    catalog: Optional[CatalogInput] = None,
    dataset_id: Optional[str] = None,
    preview_rows: Optional[int] = None,
    storage: Optional[StorageBackend] = None,
) -> PublishedDataset:
    """Publish a DataFrame and upload README (catalog embedded in code)."""

    pr = resolve_preview_rows(preview_rows)
    storage = storage or storage_from_env()

    catalog_obj: Optional[DatasetCatalog] = None
    if catalog is not None:
        catalog_obj = coerce_catalog(catalog)
        if dataset_id and catalog_obj.id != dataset_id:
            raise ValidationError("catalog id does not match dataset_id")

    if dataset_id is None:
        if catalog_obj is None:
            raise ValidationError("dataset_id or catalog is required")
        dataset_id = catalog_obj.id

    published = publish_dataframe(
        storage,
        dataset_id=dataset_id,
        df=df,
        preview_rows=pr,
        catalog=catalog_obj,
    )

    readme = producer_readme_path(producer_dir)
    if readme.exists():
        upload_readme(storage, dataset_id=dataset_id, readme_path=readme)

    return published


def publish_table_from_dir(
    producer_dir: Path,
    *,
    table: pa.Table,
    catalog: Optional[CatalogInput] = None,
    dataset_id: Optional[str] = None,
    preview_rows: Optional[int] = None,
    storage: Optional[StorageBackend] = None,
) -> PublishedDataset:
    pr = resolve_preview_rows(preview_rows)
    storage = storage or storage_from_env()

    catalog_obj: Optional[DatasetCatalog] = None
    if catalog is not None:
        catalog_obj = coerce_catalog(catalog)
        if dataset_id and catalog_obj.id != dataset_id:
            raise ValidationError("catalog id does not match dataset_id")

    if dataset_id is None:
        if catalog_obj is None:
            raise ValidationError("dataset_id or catalog is required")
        dataset_id = catalog_obj.id

    published = publish_table(
        storage,
        dataset_id=dataset_id,
        table=table,
        preview_rows=pr,
        catalog=catalog_obj,
    )

    readme = producer_readme_path(producer_dir)
    if readme.exists():
        upload_readme(storage, dataset_id=dataset_id, readme_path=readme)

    return published
