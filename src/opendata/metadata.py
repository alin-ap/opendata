from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from .errors import ValidationError
from .ids import validate_dataset_id


@dataclass(frozen=True)
class SourceInfo:
    """Structured provenance for a dataset."""

    provider: str
    homepage: Optional[str] = None
    dataset: Optional[str] = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> SourceInfo:
        def _req(key: str) -> str:
            v = data.get(key)
            if not isinstance(v, str) or not v.strip():
                raise ValidationError(f"missing required field: source.{key}")
            return v.strip()

        def _opt(key: str) -> Optional[str]:
            v = data.get(key)
            if v is None:
                return None
            if not isinstance(v, str) or not v.strip():
                raise ValidationError(f"source.{key} must be a non-empty string")
            return v.strip()

        return SourceInfo(
            provider=_req("provider"), homepage=_opt("homepage"), dataset=_opt("dataset")
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"provider": self.provider}
        if self.homepage:
            out["homepage"] = self.homepage
        if self.dataset:
            out["dataset"] = self.dataset
        return out


@dataclass(frozen=True)
class GeoInfo:
    """Optional geographic scope for a dataset."""

    scope: str
    countries: list[str] = field(default_factory=list)
    regions: list[str] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> GeoInfo:
        scope_raw = data.get("scope")
        if not isinstance(scope_raw, str) or not scope_raw.strip():
            raise ValidationError("geo.scope must be a non-empty string")
        scope = scope_raw.strip()
        if scope not in {"global", "region", "country", "multi"}:
            raise ValidationError("geo.scope must be one of: global, region, country, multi")

        def _list(key: str) -> list[str]:
            raw = data.get(key, [])
            if raw is None:
                return []
            if not isinstance(raw, list):
                raise ValidationError(f"geo.{key} must be a list")
            return [str(x) for x in raw]

        return GeoInfo(scope=scope, countries=_list("countries"), regions=_list("regions"))

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"scope": self.scope}
        if self.countries:
            out["countries"] = list(self.countries)
        if self.regions:
            out["regions"] = list(self.regions)
        return out


@dataclass(frozen=True)
class DatasetMetadata:
    """Dataset metadata stored alongside producer code.

    This is intended to be human-authored (YAML) and validated by both the SDK and
    registry tooling.

    NOTE: meta_version defaults to 2; other versions are unsupported.
    """

    meta_version: int
    id: str
    title: str
    description: str
    license: str
    repo: str
    source: SourceInfo
    topics: list[str] = field(default_factory=list)
    owners: list[str] = field(default_factory=list)
    frequency: Optional[str] = None
    geo: Optional[GeoInfo] = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> DatasetMetadata:
        raw_version = data.get("meta_version", 2)
        try:
            meta_version = int(raw_version)
        except (TypeError, ValueError) as e:
            raise ValidationError("meta_version must be an int") from e
        if meta_version != 2:
            raise ValidationError(f"unsupported meta_version: {meta_version}; expected 2")

        dataset_id = str(data.get("id", ""))
        validate_dataset_id(dataset_id)

        def _req(key: str) -> str:
            v = data.get(key)
            if not isinstance(v, str) or not v.strip():
                raise ValidationError(f"missing required field: {key}")
            return v.strip()

        def _list(key: str) -> list[str]:
            raw = data.get(key, [])
            if raw is None:
                return []
            if not isinstance(raw, list):
                raise ValidationError(f"{key} must be a list")
            return [str(x) for x in raw]

        topics = _list("topics")
        owners = _list("owners")

        frequency = data.get("frequency")
        if frequency is not None and not isinstance(frequency, str):
            raise ValidationError("frequency must be a string")

        source_raw = data.get("source")
        if not isinstance(source_raw, dict):
            raise ValidationError("source must be a mapping")
        source = SourceInfo.from_dict(source_raw)

        geo_raw = data.get("geo")
        geo: Optional[GeoInfo] = None
        if geo_raw is not None:
            if not isinstance(geo_raw, dict):
                raise ValidationError("geo must be a mapping")
            geo = GeoInfo.from_dict(geo_raw)

        return DatasetMetadata(
            meta_version=meta_version,
            id=dataset_id,
            title=_req("title"),
            description=_req("description"),
            license=_req("license"),
            repo=_req("repo"),
            source=source,
            topics=topics,
            owners=owners,
            frequency=frequency,
            geo=geo,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "meta_version": self.meta_version,
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "license": self.license,
            "repo": self.repo,
            "source": self.source.to_dict(),
        }
        if self.topics:
            data["topics"] = list(self.topics)
        if self.owners:
            data["owners"] = list(self.owners)
        if self.frequency:
            data["frequency"] = self.frequency
        if self.geo:
            data["geo"] = self.geo.to_dict()
        return data


def load_metadata(path: Path) -> DatasetMetadata:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValidationError("metadata file must contain a mapping")
    return DatasetMetadata.from_dict(raw)


def save_metadata(path: Path, meta: DatasetMetadata, *, include_meta_version: bool = True) -> None:
    data = meta.to_dict()
    if not include_meta_version:
        data.pop("meta_version", None)
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=False)
    path.write_text(text, encoding="utf-8")
