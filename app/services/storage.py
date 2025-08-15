import os
import uuid
from typing import BinaryIO, Optional
from pydantic import HttpUrl
from starlette.datastructures import UploadFile
import boto3

STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "s3")

def _safe_key(prefix: str, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return f"{prefix}/{uuid.uuid4().hex}{ext}"

def _content_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in {".png"}:
        return "image/png"
    if ext in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if ext in {".webp"}:
        return "image/webp"
    return "application/octet-stream"

def _ensure_image(filename: str):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError("Imagem deve ser PNG, JPG/JPEG ou WEBP")

def _max_size_ok(file: UploadFile, max_mb: int = 5):
    if hasattr(file, "size") and file.size:
        return file.size <= max_mb * 1024 * 1024
    return True

def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT_URL"),
        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
        region_name=os.getenv("S3_REGION", "us-east-1"),
    )

def _s3_bucket():
    return os.getenv("S3_BUCKET", "midia")

def _media_root():
    return os.getenv("MEDIA_ROOT", "/app/media")

def _media_base_url():
    return os.getenv("MEDIA_BASE_URL", "http://localhost:8000/media")

def store_image(prefix: str, file: UploadFile) -> str:
    """Armazena uma imagem em S3 ou disco local e retorna a URL pública."""
    _ensure_image(file.filename or "")
    if not _max_size_ok(file):
        raise ValueError("Arquivo excede o limite de 5MB")
    key = _safe_key(prefix, file.filename or "imagem")

    if STORAGE_BACKEND == "local":
        root = _media_root()
        os.makedirs(os.path.join(root, prefix), exist_ok=True)
        dest_path = os.path.join(root, key.split("/", 1)[1])
        with open(dest_path, "wb") as out:
            out.write(file.file.read())
        return f"{_media_base_url().rstrip('/')}/{key.split('/',1)[1]}"
    else:
        client = _s3_client()
        content_type = _content_type(file.filename or "")
        client.put_object(
            Bucket=_s3_bucket(),
            Key=key,
            Body=file.file.read(),
            ContentType=content_type,
            ACL="public-read",
        )
        endpoint = os.getenv("S3_PUBLIC_ENDPOINT") or os.getenv("S3_ENDPOINT_URL")
        if endpoint and "http" in endpoint:
            return f"{endpoint.rstrip('/')}/{_s3_bucket()}/{key}"
        return f"https://{_s3_bucket()}.s3.amazonaws.com/{key}"
