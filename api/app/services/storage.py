import hashlib
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile


@dataclass(frozen=True)
class StoredFile:
    storage_file_name: str
    file_path: str
    file_size: int
    sha256: str


def _safe_ext(content_type: str, original_name: str) -> str:
    # Minimum MVP: sadece jpeg
    # content_type güvenilmez olabilir, ama burada basit tutuyoruz.
    if content_type in ("image/jpeg", "image/jpg", "image/pjpeg"):
        return ".jpg"
    # fallback: orijinal isimden uzantı çek
    ext = os.path.splitext(original_name)[1].lower()
    return ext if ext else ".bin"


async def save_upload_to_storage(upload: UploadFile, storage_dir: str) -> StoredFile:
    Path(storage_dir).mkdir(parents=True, exist_ok=True)

    ext = _safe_ext(upload.content_type or "", upload.filename or "upload")
    storage_file_name = f"{uuid.uuid4().hex}{ext}"
    abs_path = str(Path(storage_dir) / storage_file_name)

    h = hashlib.sha256()
    size = 0

    # Stream copy (memory blow-up yok)
    with open(abs_path, "wb") as f:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
            h.update(chunk)
            size += len(chunk)

    return StoredFile(
        storage_file_name=storage_file_name,
        file_path=abs_path,
        file_size=size,
        sha256=h.hexdigest(),
    )