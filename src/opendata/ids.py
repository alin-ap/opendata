from __future__ import annotations

import re

from .errors import DatasetIdError

DATASET_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*$")


def validate_dataset_id(dataset_id: str) -> str:
    """Validate and return dataset_id.

    Dataset IDs are canonical and used to derive storage keys, so this should be
    enforced everywhere (SDK + server-side).
    """

    if not DATASET_ID_RE.fullmatch(dataset_id):
        raise DatasetIdError(
            "invalid dataset_id; expected 'namespace/name' with lowercase letters, digits, '-'. "
            f"got: {dataset_id!r}"
        )
    return dataset_id


def split_dataset_id(dataset_id: str) -> tuple[str, str]:
    dataset_id = validate_dataset_id(dataset_id)
    namespace, name = dataset_id.split("/", 1)
    return namespace, name


def dataset_prefix(dataset_id: str) -> str:
    namespace, name = split_dataset_id(dataset_id)
    return f"datasets/{namespace}/{name}"


def data_key(dataset_id: str) -> str:
    return f"{dataset_prefix(dataset_id)}/data.parquet"


def metadata_key(dataset_id: str) -> str:
    return f"{dataset_prefix(dataset_id)}/metadata.json"


def readme_key(dataset_id: str) -> str:
    return f"{dataset_prefix(dataset_id)}/README.md"
