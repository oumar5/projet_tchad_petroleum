"""Storage abstraction with two backends: local disk and S3-compatible (MinIO).

Switch via STORAGE_BACKEND=local|s3 in service settings.
"""
from .backend import LocalDiskStorage, S3Storage, StorageBackend, build_storage

__all__ = ["LocalDiskStorage", "S3Storage", "StorageBackend", "build_storage"]
