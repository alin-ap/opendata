from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, cast

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .hashing import sha256_bytes, sha256_file
from .ids import (
    data_key,
    metadata_key,
    readme_key,
    validate_dataset_id,
)
from .storage.base import StorageBackend
from .versioning import utc_now_iso


def _canonical_json_bytes(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _parquet_schema_columns(path: Path) -> list[dict[str, str]]:
    pf = pq.ParquetFile(path)
    schema = pf.schema_arrow
    return [{"name": field.name, "type": str(field.type)} for field in schema]


def _parquet_row_count(path: Path) -> int:
    pf = pq.ParquetFile(path)
    md = pf.metadata
    return int(md.num_rows) if md is not None else 0


def _json_sanitize(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return isoformat()
    return str(value)


def _parquet_preview_json(path: Path, *, preview_rows: int) -> dict[str, Any]:
    pf = pq.ParquetFile(path)

    batches: list[pa.RecordBatch] = []
    remaining = max(int(preview_rows), 0)
    if remaining == 0:
        table = pa.table({})
    else:
        for batch in pf.iter_batches(batch_size=min(remaining, 1024)):
            batches.append(batch)
            remaining -= int(batch.num_rows)
            if remaining <= 0:
                break
        table = pa.Table.from_batches(batches) if batches else pa.table({})
        if preview_rows > 0:
            table = table.slice(0, preview_rows)

    rows_raw = table.to_pylist()
    rows = [{k: _json_sanitize(v) for k, v in row.items()} for row in rows_raw]

    return {
        "generated_at": utc_now_iso(),
        "columns": list(table.column_names),
        "rows": rows,
    }


def upload_readme(storage: StorageBackend, *, dataset_id: str, readme_path: Path) -> str:
    """Upload `README.md` to a stable dataset key."""

    validate_dataset_id(dataset_id)
    key = readme_key(dataset_id)
    storage.put_bytes(key, readme_path.read_bytes(), content_type="text/markdown; charset=utf-8")
    return key


class PublishedDataset:
    def __init__(
        self,
        *,
        dataset_id: str,
        updated_at: str,
        data_key: str,
        metadata_key: str,
        row_count: int,
        data_size_bytes: int,
        checksum_sha256: str,
        columns: list[dict[str, str]],
        preview: Optional[dict[str, Any]] = None,
    ) -> None:
        self.dataset_id = dataset_id
        self.updated_at = updated_at
        self.data_key = data_key
        self.metadata_key = metadata_key
        self.row_count = row_count
        self.data_size_bytes = data_size_bytes
        self.checksum_sha256 = checksum_sha256
        self.columns = columns
        self.preview = preview

    def metadata(self) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "dataset_id": self.dataset_id,
            "updated_at": self.updated_at,
            "data_key": self.data_key,
            "metadata_key": self.metadata_key,
            "row_count": self.row_count,
            "data_size_bytes": self.data_size_bytes,
            "checksum_sha256": self.checksum_sha256,
            "format": "parquet",
            "columns": self.columns,
        }
        if self.preview is not None:
            meta["preview"] = self.preview
        return meta


def publish_parquet_file(
    storage: StorageBackend,
    *,
    dataset_id: str,
    parquet_path: Path,
    write_metadata: bool = True,
    updated_at: Optional[str] = None,
    preview_rows: int = 100,
) -> PublishedDataset:
    """Publish a parquet file + metadata (optional preview in metadata).

    This is the low-level primitive used by `opendata.push()` and the CLI.
    """

    validate_dataset_id(dataset_id)

    dk = data_key(dataset_id)
    mk = metadata_key(dataset_id)

    row_count = _parquet_row_count(parquet_path)
    columns = _parquet_schema_columns(parquet_path)

    checksum_sha256 = sha256_file(parquet_path)
    data_size_bytes = int(parquet_path.stat().st_size)

    preview_obj = None
    if preview_rows > 0:
        preview_obj = _parquet_preview_json(parquet_path, preview_rows=preview_rows)

    storage.put_bytes(dk, parquet_path.read_bytes(), content_type="application/octet-stream")

    published = PublishedDataset(
        dataset_id=dataset_id,
        updated_at=updated_at or utc_now_iso(),
        data_key=dk,
        metadata_key=mk,
        row_count=row_count,
        data_size_bytes=data_size_bytes,
        checksum_sha256=checksum_sha256,
        columns=columns,
        preview=preview_obj,
    )

    if write_metadata:
        storage.put_bytes(
            mk, _canonical_json_bytes(published.metadata()), content_type="application/json"
        )

    return published


def _table_schema_columns(table: pa.Table) -> list[dict[str, str]]:
    return [{"name": field.name, "type": str(field.type)} for field in table.schema]


def _table_preview_json(table: pa.Table, *, preview_rows: int) -> dict[str, Any]:
    if preview_rows <= 0:
        view = table.slice(0, 0)
    else:
        view = table.slice(0, min(int(preview_rows), int(table.num_rows)))

    rows_raw = view.to_pylist()
    rows = [{k: _json_sanitize(v) for k, v in row.items()} for row in rows_raw]

    return {
        "generated_at": utc_now_iso(),
        "columns": list(view.column_names),
        "rows": rows,
    }


def _table_to_parquet_bytes(table: pa.Table) -> bytes:
    sink = pa.BufferOutputStream()
    pq.write_table(table, sink)
    return cast(bytes, sink.getvalue().to_pybytes())


def publish_table(
    storage: StorageBackend,
    *,
    dataset_id: str,
    table: pa.Table,
    write_metadata: bool = True,
    updated_at: Optional[str] = None,
    preview_rows: int = 100,
) -> PublishedDataset:
    """Publish an Arrow table as parquet bytes.

    This avoids requiring a local `data.parquet` file.
    """

    validate_dataset_id(dataset_id)

    dk = data_key(dataset_id)
    mk = metadata_key(dataset_id)

    row_count = int(table.num_rows)
    columns = _table_schema_columns(table)

    preview_obj = None
    if preview_rows > 0:
        preview_obj = _table_preview_json(table, preview_rows=preview_rows)

    parquet_bytes = _table_to_parquet_bytes(table)
    data_size_bytes = len(parquet_bytes)

    checksum_sha256 = sha256_bytes(parquet_bytes)

    storage.put_bytes(dk, parquet_bytes, content_type="application/octet-stream")

    published = PublishedDataset(
        dataset_id=dataset_id,
        updated_at=updated_at or utc_now_iso(),
        data_key=dk,
        metadata_key=mk,
        row_count=row_count,
        data_size_bytes=data_size_bytes,
        checksum_sha256=checksum_sha256,
        columns=columns,
        preview=preview_obj,
    )

    if write_metadata:
        storage.put_bytes(
            mk, _canonical_json_bytes(published.metadata()), content_type="application/json"
        )

    return published


def publish_dataframe(
    storage: StorageBackend,
    *,
    dataset_id: str,
    df: pd.DataFrame,
    write_metadata: bool = True,
    updated_at: Optional[str] = None,
    preview_rows: int = 100,
) -> PublishedDataset:
    """Publish a pandas DataFrame without writing a parquet file."""

    table = pa.Table.from_pandas(df, preserve_index=False)
    return publish_table(
        storage,
        dataset_id=dataset_id,
        table=table,
        write_metadata=write_metadata,
        updated_at=updated_at,
        preview_rows=preview_rows,
    )
