from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import NotFoundError
from .ids import readme_key, validate_dataset_id
from .metadata import DatasetMetadata, load_metadata
from .storage.base import StorageBackend
from .versioning import utc_now_iso


def _canonical_json_bytes(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _empty_index() -> dict[str, Any]:
    return {"meta_version": 1, "generated_at": utc_now_iso(), "datasets": []}


class Registry:
    """A minimal dataset registry stored as a single JSON index.

    This is a pragmatic bootstrap: it keeps a searchable list of datasets in
    `index.json`, which can be served directly by R2 (or any other object store).
    """

    def __init__(self, storage: StorageBackend, *, index_key: str = "index.json") -> None:
        self._storage = storage
        self._index_key = index_key

    @property
    def index_key(self) -> str:
        return self._index_key

    def load(self) -> dict[str, Any]:
        try:
            raw = self._storage.get_bytes(self._index_key)
        except NotFoundError:
            return _empty_index()

        data = json.loads(raw)
        if not isinstance(data, dict):
            return _empty_index()
        if data.get("meta_version") != 1:
            return _empty_index()
        if not isinstance(data.get("datasets"), list):
            return _empty_index()
        return data

    def save(self, index: dict[str, Any]) -> None:
        index = dict(index)
        index["meta_version"] = 1
        index["generated_at"] = utc_now_iso()
        self._storage.put_bytes(
            self._index_key, _canonical_json_bytes(index), content_type="application/json"
        )

    def register(self, meta: DatasetMetadata) -> None:
        validate_dataset_id(meta.id)

        index = self.load()
        datasets = list(index.get("datasets", []))

        entry = {
            "id": meta.id,
            "title": meta.title,
            "description": meta.description,
            "license": meta.license,
            "source": meta.source,
            "repo": meta.repo,
            "readme_key": readme_key(meta.id),
            "tags": list(meta.tags),
            "owners": list(meta.owners),
        }
        if meta.frequency:
            entry["frequency"] = meta.frequency
        if meta.versioning:
            entry["versioning"] = meta.versioning

        replaced = False
        for i, existing in enumerate(datasets):
            if isinstance(existing, dict) and existing.get("id") == meta.id:
                datasets[i] = {**existing, **entry}
                replaced = True
                break
        if not replaced:
            datasets.append(entry)

        datasets.sort(key=lambda d: str(d.get("id", "")))
        index["datasets"] = datasets
        self.save(index)

    def register_from_file(self, meta_path: Path) -> DatasetMetadata:
        meta = load_metadata(meta_path)
        self.register(meta)
        return meta

    def refresh_stats(self, dataset_id: str) -> None:
        """Refresh index stats for a dataset from its `<dataset>/latest.json`."""

        validate_dataset_id(dataset_id)
        index = self.load()
        datasets = list(index.get("datasets", []))

        try:
            latest_raw = self._storage.get_bytes(f"datasets/{dataset_id}/latest.json")
        except NotFoundError:
            return

        latest = json.loads(latest_raw)
        if not isinstance(latest, dict):
            return

        stats: dict[str, Any] = {}
        for key in [
            "version",
            "updated_at",
            "row_count",
            "data_size_bytes",
            "data_key",
            "schema_key",
            "preview_key",
            "checksum_sha256",
            "schema_hash_sha256",
        ]:
            if key in latest:
                stats[key] = latest[key]

        for i, existing in enumerate(datasets):
            if isinstance(existing, dict) and existing.get("id") == dataset_id:
                datasets[i] = {**existing, **stats}
                break

        index["datasets"] = datasets
        self.save(index)

    def build_from_producer_root(self, producer_root: Path) -> dict[str, Any]:
        """(Re)build `index.json` from producer metadata + latest pointers.

        This avoids races when multiple producers publish in parallel: only this
        method writes `index.json`.
        """

        meta_paths = sorted(producer_root.glob("**/opendata.yaml"))
        datasets: list[dict[str, Any]] = []

        for meta_path in meta_paths:
            try:
                meta = load_metadata(meta_path)
            except Exception:
                continue

            entry: dict[str, Any] = {
                "id": meta.id,
                "title": meta.title,
                "description": meta.description,
                "license": meta.license,
                "source": meta.source,
                "repo": meta.repo,
                "readme_key": readme_key(meta.id),
                "tags": list(meta.tags),
                "owners": list(meta.owners),
            }
            if meta.frequency:
                entry["frequency"] = meta.frequency
            if meta.versioning:
                entry["versioning"] = meta.versioning

            # Merge latest stats if available.
            try:
                latest_raw = self._storage.get_bytes(f"datasets/{meta.id}/latest.json")
            except NotFoundError:
                datasets.append(entry)
                continue

            try:
                latest = json.loads(latest_raw)
            except Exception:
                datasets.append(entry)
                continue
            if not isinstance(latest, dict):
                datasets.append(entry)
                continue

            for key in [
                "version",
                "updated_at",
                "row_count",
                "data_size_bytes",
                "data_key",
                "schema_key",
                "preview_key",
                "checksum_sha256",
                "schema_hash_sha256",
            ]:
                if key in latest:
                    entry[key] = latest[key]

            datasets.append(entry)

        datasets.sort(key=lambda d: str(d.get("id", "")))
        index = {"meta_version": 1, "generated_at": utc_now_iso(), "datasets": datasets}
        self.save(index)
        return index
