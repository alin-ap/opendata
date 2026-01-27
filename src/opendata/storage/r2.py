from __future__ import annotations

import os
from typing import Optional, cast

from ..errors import NotFoundError, StorageError
from .base import StorageBackend


class R2Config:
    def __init__(
        self,
        *,
        endpoint_url: str,
        bucket: str,
        access_key_id: str,
        secret_access_key: str,
        region: str = "auto",
    ) -> None:
        self.endpoint_url = endpoint_url
        self.bucket = bucket
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.region = region

    @staticmethod
    def from_env() -> R2Config:
        """Load config from environment variables.

        Required:
        - OPENDATA_R2_ENDPOINT_URL
        - OPENDATA_R2_BUCKET
        - OPENDATA_R2_ACCESS_KEY_ID
        - OPENDATA_R2_SECRET_ACCESS_KEY

        Optional:
        - OPENDATA_R2_REGION (default: auto)
        """

        endpoint_url = os.environ.get("OPENDATA_R2_ENDPOINT_URL", "").strip()
        bucket = os.environ.get("OPENDATA_R2_BUCKET", "").strip()
        access_key_id = os.environ.get("OPENDATA_R2_ACCESS_KEY_ID", "").strip()
        secret_access_key = os.environ.get("OPENDATA_R2_SECRET_ACCESS_KEY", "").strip()
        region = os.environ.get("OPENDATA_R2_REGION", "auto").strip() or "auto"

        missing = [
            name
            for name, value in [
                ("OPENDATA_R2_ENDPOINT_URL", endpoint_url),
                ("OPENDATA_R2_BUCKET", bucket),
                ("OPENDATA_R2_ACCESS_KEY_ID", access_key_id),
                ("OPENDATA_R2_SECRET_ACCESS_KEY", secret_access_key),
            ]
            if not value
        ]
        if missing:
            raise StorageError(
                "missing R2 env vars: "
                + ", ".join(missing)
                + ". Install with 'pip install -e .[r2]'."
            )

        return R2Config(
            endpoint_url=endpoint_url,
            bucket=bucket,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            region=region,
        )


class R2Storage(StorageBackend):
    """Cloudflare R2 storage backend (S3 compatible).

    Requires optional dependency: `pip install -e .[r2]`.
    """

    def __init__(self, cfg: R2Config) -> None:
        try:
            import boto3  # type: ignore
            from botocore.config import Config  # type: ignore
        except Exception as e:  # pragma: no cover
            raise StorageError("boto3 is required for R2Storage; install extras 'r2'") from e

        self._bucket = cfg.bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=cfg.endpoint_url,
            aws_access_key_id=cfg.access_key_id,
            aws_secret_access_key=cfg.secret_access_key,
            region_name=cfg.region,
            config=Config(signature_version="s3v4"),
        )

    @staticmethod
    def from_env() -> R2Storage:
        return R2Storage(R2Config.from_env())

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False

    def get_bytes(self, key: str) -> bytes:
        try:
            resp = self._client.get_object(Bucket=self._bucket, Key=key)
            return cast(bytes, resp["Body"].read())
        except Exception as e:
            raise NotFoundError(f"not found: {key}") from e

    def put_bytes(self, key: str, data: bytes, *, content_type: Optional[str] = None) -> None:
        kwargs: dict[str, object] = {"Bucket": self._bucket, "Key": key, "Body": data}
        if content_type:
            kwargs["ContentType"] = content_type
        try:
            self._client.put_object(**kwargs)
        except Exception as e:
            raise StorageError(f"failed to put object: {key}") from e
