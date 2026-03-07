import hashlib
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile
import boto3

from app.core.settings import settings


@dataclass(frozen=True)
class StoredFile:
    storage_file_name: str
    file_path: str
    file_size: int
    sha256: str


def _safe_ext(content_type: str, original_name: str) -> str:
    if content_type in ("image/jpeg", "image/jpg", "image/pjpeg"):
        return ".jpg"
    ext = os.path.splitext(original_name)[1].lower()
    return ext if ext else ".bin"


async def save_upload_to_storage(upload: UploadFile, storage_dir: str) -> StoredFile:
    """
    Saves file to S3. For local mocks or testing without AWS credentials,
    it falls back to local storage if AWS keys aren't strictly provided.
    """
    ext = _safe_ext(upload.content_type or "", upload.filename or "upload")
    storage_file_name = f"{uuid.uuid4().hex}{ext}"

    # Read fully into memory to get hash & size (safe for small receipts ~2-5MB)
    content = await upload.read()
    size = len(content)
    file_hash = hashlib.sha256(content).hexdigest()

    # Determine if we should use S3 or Local Mock
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION_NAME
        )
        s3.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=storage_file_name,
            Body=content,
            ContentType=upload.content_type or "image/jpeg"
        )
        # file_path in DB will store the S3 URI
        file_path = f"s3://{settings.AWS_S3_BUCKET_NAME}/{storage_file_name}"
    else:
        # Fallback to local storage
        Path(storage_dir).mkdir(parents=True, exist_ok=True)
        file_path = str(Path(storage_dir) / storage_file_name)
        with open(file_path, "wb") as f:
            f.write(content)

    return StoredFile(
        storage_file_name=storage_file_name,
        file_path=file_path,
        file_size=size,
        sha256=file_hash,
    )