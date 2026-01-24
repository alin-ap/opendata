from __future__ import annotations

import re

from .errors import DatasetIdError, VersionError

DATASET_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*$")
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


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


def validate_version(version: str) -> str:
    if not VERSION_RE.fullmatch(version):
        raise VersionError(
            "invalid version; expected 1-64 chars (letters, digits, '.', '_', '-') and no slashes. "
            f"got: {version!r}"
        )
    return version


def dataset_prefix(dataset_id: str) -> str:
    namespace, name = split_dataset_id(dataset_id)
    return f"datasets/{namespace}/{name}"


def data_key(dataset_id: str, version: str) -> str:
    version = validate_version(version)
    return f"{dataset_prefix(dataset_id)}/{version}/data.parquet"


def schema_key(dataset_id: str, version: str) -> str:
    version = validate_version(version)
    return f"{dataset_prefix(dataset_id)}/{version}/schema.json"


def preview_key(dataset_id: str, version: str) -> str:
    version = validate_version(version)
    return f"{dataset_prefix(dataset_id)}/{version}/preview.json"


def latest_key(dataset_id: str) -> str:
    return f"{dataset_prefix(dataset_id)}/latest.json"


def readme_key(dataset_id: str) -> str:
    return f"{dataset_prefix(dataset_id)}/README.md"
