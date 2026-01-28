from __future__ import annotations

from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .ids import data_key, validate_dataset_id
from .metadata import CatalogInput, coerce_catalog
from .publish import publish_dataframe
from .storage import storage_from_env
from .storage.base import StorageBackend


def load(
    dataset_id: str,
    *,
    storage: Optional[StorageBackend] = None,
) -> pd.DataFrame:
    """Load a dataset into a pandas DataFrame.

    This function does not write any local cache files. Data is fetched from the
    configured storage backend and decoded in-memory.
    """

    storage = storage or storage_from_env()

    validate_dataset_id(dataset_id)

    parquet_bytes = storage.get_bytes(data_key(dataset_id))
    table = pq.read_table(pa.BufferReader(parquet_bytes))
    return table.to_pandas()


def push(
    df: pd.DataFrame,
    *,
    catalog: CatalogInput,
    storage: Optional[StorageBackend] = None,
) -> None:
    """Publish a pandas DataFrame to storage as Parquet."""

    storage = storage or storage_from_env()
    cat = coerce_catalog(catalog)
    publish_dataframe(storage, dataset_id=cat.id, df=df, catalog=cat)
