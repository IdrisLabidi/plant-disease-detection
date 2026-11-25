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
