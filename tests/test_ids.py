from __future__ import annotations

import pytest

from opendata.errors import DatasetIdError
from opendata.ids import (
    data_key,
    metadata_key,
    preview_key,
    readme_key,
    validate_dataset_id,
)


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


def test_key_layout() -> None:
    dataset_id = "official/us-stock-daily"
    assert data_key(dataset_id) == "datasets/official/us-stock-daily/data.parquet"
    assert preview_key(dataset_id) == "datasets/official/us-stock-daily/preview.json"
    assert metadata_key(dataset_id) == "datasets/official/us-stock-daily/metadata.json"
    assert readme_key(dataset_id) == "datasets/official/us-stock-daily/README.md"
