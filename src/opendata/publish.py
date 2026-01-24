from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pyarrow as pa
import pyarrow.parquet as pq

from .hashing import sha256_bytes, sha256_file
from .ids import (
    data_key,
    latest_key,
    preview_key,
    readme_key,
    schema_key,
    validate_dataset_id,
    validate_version,
)
from .storage.base import StorageBackend
from .versioning import utc_now_iso


def _canonical_json_bytes(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _parquet_schema_json(path: Path) -> dict[str, Any]:
    pf = pq.ParquetFile(path)
    schema = pf.schema_arrow
    return {
        "format": "parquet",
        "columns": [{"name": field.name, "type": str(field.type)} for field in schema],
    }


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


def _parquet_preview_json(
    path: Path, *, dataset_id: str, version: str, preview_rows: int
) -> dict[str, Any]:
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
        "dataset_id": dataset_id,
        "version": version,
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


class PublishedVersion:
    def __init__(
        self,
        *,
        dataset_id: str,
        version: str,
        updated_at: str,
        data_key: str,
        schema_key: str,
        preview_key: str,
        row_count: int,
        data_size_bytes: int,
        checksum_sha256: str,
        schema_hash_sha256: str,
    ) -> None:
        self.dataset_id = dataset_id
        self.version = version
        self.updated_at = updated_at
        self.data_key = data_key
        self.schema_key = schema_key
        self.preview_key = preview_key
        self.row_count = row_count
        self.data_size_bytes = data_size_bytes
        self.checksum_sha256 = checksum_sha256
        self.schema_hash_sha256 = schema_hash_sha256

    def latest_pointer(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "updated_at": self.updated_at,
            "data_key": self.data_key,
            "schema_key": self.schema_key,
            "preview_key": self.preview_key,
            "row_count": self.row_count,
            "data_size_bytes": self.data_size_bytes,
            "checksum_sha256": self.checksum_sha256,
            "schema_hash_sha256": self.schema_hash_sha256,
        }


def publish_parquet_file(
    storage: StorageBackend,
    *,
    dataset_id: str,
    parquet_path: Path,
    version: str,
    write_latest: bool = True,
    updated_at: Optional[str] = None,
    preview_rows: int = 100,
) -> PublishedVersion:
    """Publish a parquet file + schema + latest pointer.

    This is the low-level primitive used by `opendata.push()` and the CLI.
    """

    validate_dataset_id(dataset_id)
    validate_version(version)

    dk = data_key(dataset_id, version)
    sk = schema_key(dataset_id, version)
    pk = preview_key(dataset_id, version)
    lk = latest_key(dataset_id)

    row_count = _parquet_row_count(parquet_path)
    schema_obj = _parquet_schema_json(parquet_path)
    schema_bytes = _canonical_json_bytes(schema_obj)

    checksum_sha256 = sha256_file(parquet_path)
    schema_hash_sha256 = sha256_bytes(schema_bytes)
    data_size_bytes = int(parquet_path.stat().st_size)

    preview_obj = _parquet_preview_json(
        parquet_path, dataset_id=dataset_id, version=version, preview_rows=preview_rows
    )
    preview_bytes = _canonical_json_bytes(preview_obj)

    storage.upload_file(dk, parquet_path, content_type="application/octet-stream")
    storage.put_bytes(sk, schema_bytes, content_type="application/json")
    storage.put_bytes(pk, preview_bytes, content_type="application/json")

    published = PublishedVersion(
        dataset_id=dataset_id,
        version=version,
        updated_at=updated_at or utc_now_iso(),
        data_key=dk,
        schema_key=sk,
        preview_key=pk,
        row_count=row_count,
        data_size_bytes=data_size_bytes,
        checksum_sha256=checksum_sha256,
        schema_hash_sha256=schema_hash_sha256,
    )

    if write_latest:
        storage.put_bytes(
            lk, _canonical_json_bytes(published.latest_pointer()), content_type="application/json"
        )

    return published
