from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Union

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
class DatasetCatalog:
    """Human-authored catalog fields embedded in producer code."""

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
    def from_dict(data: dict[str, Any]) -> DatasetCatalog:
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

        return DatasetCatalog(
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

    def to_catalog_dict(self) -> dict[str, Any]:
        data = self.to_dict()
        data.pop("id", None)
        return data


CatalogInput = Union[DatasetCatalog, dict[str, Any]]


def coerce_catalog(raw: CatalogInput) -> DatasetCatalog:
    if isinstance(raw, DatasetCatalog):
        return raw
    if isinstance(raw, dict):
        return DatasetCatalog.from_dict(raw)
    raise ValidationError("catalog must be a DatasetCatalog or dict")
