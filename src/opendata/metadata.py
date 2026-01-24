from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from .errors import ValidationError
from .ids import validate_dataset_id


@dataclass(frozen=True)
class DatasetMetadata:
    """Minimal dataset metadata stored alongside producer code.

    This is intended to be human-authored (YAML) and validated by both the SDK and
    server-side registry.
    """

    meta_version: int
    id: str
    title: str
    description: str
    license: str
    source: str
    repo: str
    tags: list[str] = field(default_factory=list)
    owners: list[str] = field(default_factory=list)
    frequency: Optional[str] = None
    versioning: Optional[str] = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> DatasetMetadata:
        meta_version = int(data.get("meta_version", 0))
        if meta_version != 1:
            raise ValidationError(f"unsupported meta_version: {meta_version}; expected 1")

        dataset_id = str(data.get("id", ""))
        validate_dataset_id(dataset_id)

        def _req(key: str) -> str:
            v = data.get(key)
            if not isinstance(v, str) or not v.strip():
                raise ValidationError(f"missing required field: {key}")
            return v.strip()

        tags_raw = data.get("tags", [])
        tags = [str(x) for x in tags_raw] if isinstance(tags_raw, list) else []

        owners_raw = data.get("owners", [])
        owners = [str(x) for x in owners_raw] if isinstance(owners_raw, list) else []

        frequency = data.get("frequency")
        if frequency is not None and not isinstance(frequency, str):
            raise ValidationError("frequency must be a string")

        versioning = data.get("versioning")
        if versioning is not None and not isinstance(versioning, str):
            raise ValidationError("versioning must be a string")

        return DatasetMetadata(
            meta_version=meta_version,
            id=dataset_id,
            title=_req("title"),
            description=_req("description"),
            license=_req("license"),
            source=_req("source"),
            repo=_req("repo"),
            tags=tags,
            owners=owners,
            frequency=frequency,
            versioning=versioning,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "meta_version": self.meta_version,
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "license": self.license,
            "source": self.source,
            "repo": self.repo,
        }
        if self.tags:
            data["tags"] = list(self.tags)
        if self.owners:
            data["owners"] = list(self.owners)
        if self.frequency:
            data["frequency"] = self.frequency
        if self.versioning:
            data["versioning"] = self.versioning
        return data


def load_metadata(path: Path) -> DatasetMetadata:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValidationError("metadata file must contain a mapping")
    return DatasetMetadata.from_dict(raw)


def save_metadata(path: Path, meta: DatasetMetadata) -> None:
    text = yaml.safe_dump(meta.to_dict(), sort_keys=False, allow_unicode=False)
    path.write_text(text, encoding="utf-8")
