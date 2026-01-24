from __future__ import annotations


class OpendataError(Exception):
    """Base exception for the OpenData SDK."""


class ValidationError(OpendataError):
    """Raised when user input/config is invalid."""


class DatasetIdError(ValidationError):
    """Raised when a dataset_id is malformed."""


class VersionError(ValidationError):
    """Raised when a dataset version is malformed."""


class NotFoundError(OpendataError):
    """Raised when an object is not found in storage."""


class StorageError(OpendataError):
    """Raised when an underlying storage operation fails."""
