
from datetime import timedelta
from io import BytesIO
import pathlib
from uuid import uuid4
from fastapi import UploadFile
from minio import Minio, S3Error
from minio.commonconfig import ComposeSource   
from app.core.config import settings

BUCKET = settings.MINIO_BUCKET

internal = Minio(
    settings.MINIO_ENDPOINT,             
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,
)

public = Minio(
    settings.MINIO_PUBLIC_ENDPOINT.split("://")[1],  
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    region="us-east-1", 
    secure=False,
)


def upload_file_to_minio(file_buffer: BytesIO, filename: str, prefix: str = "presentations", content_type: str = "application/pdf") -> str:
    ext = filename.split(".")[-1]
    obj = f"{prefix}/{uuid4()}.{ext}"

    file_buffer.seek(0)  # Always rewind
    try:
        internal.put_object(
            bucket_name=BUCKET,
            object_name=obj,
            data=file_buffer,
            length=len(file_buffer.getbuffer()),
            content_type=content_type,
        )
        return f"{settings.MINIO_PUBLIC_ENDPOINT.rstrip('/')}/{BUCKET}/{obj}"
    except S3Error as e:
        print("MinIO upload failed:", e)
        raise


def create_upload_urls(prefix: str, parts: int = 50) -> list[str]:
    """Presign <parts> PUT URLs the browser can call directly."""
    return [
        public.presigned_put_object(
            BUCKET,
            f"{prefix}/{i:05}.webm",
            expires=timedelta(hours=1),
        )
        for i in range(parts)
    ]



def compose_to_single(prefix: str, out_name: str):
    parts_iter = internal.list_objects(
        BUCKET,
        prefix=prefix,
        recursive=True,
    )

    sources = [
        ComposeSource(BUCKET, obj.object_name)  
        for obj in parts_iter
    ]
    if not sources:
        raise ValueError(f"No part found under {prefix}")

    internal.compose_object(BUCKET, out_name, sources)

def public_object_url(key: str) -> str:
    """Return a bucket-public URL usable by browsers without signing."""
    return f"{settings.MINIO_PUBLIC_ENDPOINT.rstrip('/')}/{BUCKET}/{key}"

def download_object_to_tmpfile(key: str) -> pathlib.Path:
    """
    Downloads a MinIO object to a temporary file and returns its Path.
    """
    import tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    internal.fget_object(BUCKET, key, tmp.name)
    return pathlib.Path(tmp.name)

