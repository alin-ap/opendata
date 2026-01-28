from __future__ import annotations

import json
from typing import Any

from .errors import NotFoundError
from .ids import metadata_key, validate_dataset_id
from .storage.base import StorageBackend
from .versioning import utc_now_iso


def _canonical_json_bytes(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _empty_index() -> dict[str, Any]:
    return {"generated_at": utc_now_iso(), "datasets": []}


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
        if not isinstance(data.get("datasets"), list):
            return _empty_index()
        return data

    def save(self, index: dict[str, Any]) -> None:
        index = dict(index)
        index["generated_at"] = utc_now_iso()
        self._storage.put_bytes(
            self._index_key, _canonical_json_bytes(index), content_type="application/json"
        )

    def refresh_metadata(self, dataset_id: str) -> None:
        """Refresh index entry for a dataset from its `<dataset>/metadata.json`."""

        validate_dataset_id(dataset_id)
        index = self.load()
        datasets = list(index.get("datasets", []))

        try:
            meta_raw = self._storage.get_bytes(metadata_key(dataset_id))
        except NotFoundError:
            return

        meta_payload = json.loads(meta_raw)
        if not isinstance(meta_payload, dict):
            return

        entry: dict[str, Any] = {
            "id": dataset_id,
        }
        for key in [
            "title",
            "description",
            "license",
            "source",
            "repo",
            "topics",
            "owners",
            "frequency",
            "geo",
            "updated_at",
            "row_count",
            "data_size_bytes",
        ]:
            if key in meta_payload:
                entry[key] = meta_payload[key]

        replaced = False
        for i, existing in enumerate(datasets):
            if isinstance(existing, dict) and existing.get("id") == dataset_id:
                datasets[i] = {**existing, **entry}
                replaced = True
                break
        if not replaced:
            datasets.append(entry)

        datasets.sort(key=lambda d: str(d.get("id", "")))
        index["datasets"] = datasets
        self.save(index)
