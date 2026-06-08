import hashlib
from pathlib import PurePosixPath
from pathlib import Path


def _validate_object_key(object_key: str) -> None:
    key = str(object_key or "")
    path = PurePosixPath(key)
    if not key or "\x00" in key or "\\" in key or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("invalid object key")


class BaseObjectStorage:
    def upload_bytes(self, object_key: str, content: bytes) -> dict:
        raise NotImplementedError

    def get_bytes(self, object_key: str) -> bytes:
        raise NotImplementedError

    def describe(self) -> dict:
        raise NotImplementedError

    def healthcheck(self) -> dict:
        raise NotImplementedError


class LocalObjectStorage(BaseObjectStorage):
    def __init__(self, base_path: str):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def upload_bytes(self, object_key: str, content: bytes) -> dict:
        file_path = self._object_path(object_key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        return {
            "object_key": object_key,
            "sha256": hashlib.sha256(content).hexdigest(),
            "size_bytes": len(content),
        }

    def get_bytes(self, object_key: str) -> bytes:
        return self._object_path(object_key).read_bytes()

    def describe(self) -> dict:
        return {"backend": "local", "base_path": str(self.base_path)}

    def healthcheck(self) -> dict:
        if not self.base_path.exists():
            raise FileNotFoundError(f"storage path {self.base_path} not found")
        return {"backend": "local", "base_path": str(self.base_path)}

    def _object_path(self, object_key: str) -> Path:
        _validate_object_key(object_key)
        file_path = (self.base_path / object_key).resolve()
        if not file_path.is_relative_to(self.base_path):
            raise ValueError("invalid object key")
        return file_path


class MinioObjectStorage(BaseObjectStorage):
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool):
        from minio import Minio

        self.bucket = bucket
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def upload_bytes(self, object_key: str, content: bytes) -> dict:
        from io import BytesIO

        _validate_object_key(object_key)
        self.client.put_object(self.bucket, object_key, BytesIO(content), len(content))
        return {
            "object_key": object_key,
            "sha256": hashlib.sha256(content).hexdigest(),
            "size_bytes": len(content),
        }

    def get_bytes(self, object_key: str) -> bytes:
        _validate_object_key(object_key)
        response = self.client.get_object(self.bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def describe(self) -> dict:
        return {"backend": "minio", "bucket": self.bucket}

    def healthcheck(self) -> dict:
        if not self.client.bucket_exists(self.bucket):
            raise RuntimeError(f"bucket {self.bucket} is unavailable")
        return {"backend": "minio", "bucket": self.bucket}


def create_storage(config: dict) -> BaseObjectStorage:
    if config["STORAGE_BACKEND"] == "minio":
        try:
            return MinioObjectStorage(
                endpoint=config["MINIO_ENDPOINT"],
                access_key=config["MINIO_ACCESS_KEY"],
                secret_key=config["MINIO_SECRET_KEY"],
                bucket=config["MINIO_BUCKET"],
                secure=config["MINIO_SECURE"],
            )
        except Exception:
            if not config["ALLOW_RUNTIME_FALLBACK"]:
                raise
    return LocalObjectStorage(config["LOCAL_STORAGE_PATH"])
