"""Pluggable object storage backends — local disk for dev, S3/MinIO for prod-like."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


@dataclass(frozen=True)
class StoredObject:
    """Result of a put() — opaque key + size for the caller to persist."""

    key: str
    size_bytes: int


class StorageBackend(ABC):
    """Interface used by services to store/load binary blobs.

    `key` is an opaque path-like identifier the backend understands.
    For LocalDiskStorage it is a relative path under `base_dir`.
    For S3Storage it is the S3 object key.
    """

    @abstractmethod
    def put(self, *, key: str, data: bytes, content_type: str) -> StoredObject:
        ...

    @abstractmethod
    def open(self, key: str) -> BinaryIO:
        """Returns a file-like object positioned at the start of the blob."""

    @abstractmethod
    def delete(self, key: str) -> None:
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        ...


class LocalDiskStorage(StorageBackend):
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Reject absolute keys to avoid path traversal
        clean = key.lstrip("/").replace("..", "")
        return self.base_dir / clean

    def put(self, *, key: str, data: bytes, content_type: str) -> StoredObject:
        del content_type  # unused for local backend
        target = self._path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return StoredObject(key=key, size_bytes=len(data))

    def open(self, key: str) -> BinaryIO:
        return self._path(key).open("rb")

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()


class S3Storage(StorageBackend):
    """S3 / MinIO backend (boto3 with `endpoint_url` override for MinIO)."""

    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
    ):
        import boto3  # local import — keeps import cheap when backend is "local"
        self.bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    def put(self, *, key: str, data: bytes, content_type: str) -> StoredObject:
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return StoredObject(key=key, size_bytes=len(data))

    def open(self, key: str) -> BinaryIO:
        obj = self._client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"]

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey"}:
                return False
            raise


def build_storage(
    *,
    backend: str,
    local_dir: str,
    s3_bucket: str | None = None,
    s3_endpoint: str | None = None,
    s3_access_key: str | None = None,
    s3_secret_key: str | None = None,
    s3_region: str = "us-east-1",
) -> StorageBackend:
    """Factory used by services. `backend` is 'local' or 's3'."""
    backend = (backend or "local").lower()
    if backend == "s3":
        if not s3_bucket or not s3_access_key or not s3_secret_key:
            raise ValueError(
                "STORAGE_BACKEND=s3 requires S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY"
            )
        return S3Storage(
            bucket=s3_bucket,
            endpoint_url=s3_endpoint,
            access_key=s3_access_key,
            secret_key=s3_secret_key,
            region=s3_region,
        )
    return LocalDiskStorage(local_dir)
