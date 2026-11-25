from pathlib import Path
from typing import Protocol


class ScanStorage(Protocol):
    def save(self, key: str, content: bytes) -> str: ...

    def read(self, path: str) -> bytes: ...

    def delete(self, path: str) -> None: ...

    def url(self, path: str) -> str: ...


class LocalScanStorage:
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, content: bytes) -> str:
        safe_key = Path(key)
        if safe_key.is_absolute() or ".." in safe_key.parts:
            raise ValueError("Invalid storage key")
        path = self.root / safe_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)

    def read(self, path: str) -> bytes:
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = self.root / file_path
        if not file_path.exists() or self.root not in file_path.resolve().parents:
            raise FileNotFoundError(path)
        return file_path.read_bytes()

    def delete(self, path: str | None) -> None:
        if not path:
            return
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = self.root / file_path
        if file_path.exists() and self.root in file_path.resolve().parents:
            file_path.unlink()

    def url(self, path: str) -> str:
        return f"/scans/{Path(path).stem}/image"

class CloudinaryScanStorage:
    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        import cloudinary
        import cloudinary.uploader
        import cloudinary.api

        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret

        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True
        )

    def save(self, key: str, content: bytes) -> str:
        from io import BytesIO
        import cloudinary.uploader

        safe_key = Path(key)
        if safe_key.is_absolute() or ".." in safe_key.parts:
            raise ValueError("Invalid storage key")

        # Upload the file to Cloudinary
        result = cloudinary.uploader.upload(BytesIO(content), public_id=str(safe_key), overwrite=True)
        return result['public_id']

    def read(self, path: str) -> bytes:
        raise NotImplementedError("Reading files from Cloudinary is not supported.")

    def delete(self, path: str | None) -> None:
        if not path:
            return
        import cloudinary.uploader
        cloudinary.uploader.destroy(path)

    def url(self, path: str) -> str:
        import cloudinary.utils
        return cloudinary.utils.cloudinary_url(path)[0]