from __future__ import annotations

import pytest

from opendata.errors import DatasetIdError, VersionError
from opendata.ids import data_key, latest_key, schema_key, validate_dataset_id, validate_version


def test_validate_dataset_id_ok() -> None:
    assert validate_dataset_id("official/us-stock-daily") == "official/us-stock-daily"


@pytest.mark.parametrize(
    "bad",
    [
        "Official/us-stock-daily",
        "official/us stock",
        "official/",
        "official",
        "official/us_stock",
        "../x/y",
    ],
)
def test_validate_dataset_id_bad(bad: str) -> None:
    with pytest.raises(DatasetIdError):
        validate_dataset_id(bad)


def test_validate_version_ok() -> None:
    assert validate_version("2026-01-24") == "2026-01-24"
    assert validate_version("v1.2.3") == "v1.2.3"


@pytest.mark.parametrize("bad", ["", "a" * 65, "2026/01/24", "../x"])
def test_validate_version_bad(bad: str) -> None:
    with pytest.raises(VersionError):
        validate_version(bad)


def test_key_layout() -> None:
    dataset_id = "official/us-stock-daily"
    version = "2026-01-24"
    assert (
        data_key(dataset_id, version) == "datasets/official/us-stock-daily/2026-01-24/data.parquet"
    )
    assert (
        schema_key(dataset_id, version) == "datasets/official/us-stock-daily/2026-01-24/schema.json"
    )
    assert latest_key(dataset_id) == "datasets/official/us-stock-daily/latest.json"
