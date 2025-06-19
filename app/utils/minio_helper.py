from minio import Minio
from minio.error import S3Error
from uuid import uuid4
from fastapi import UploadFile
from app.core.config import settings  

minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False
)

def upload_file_to_minio(file: UploadFile, prefix: str = "presentations") -> str:
    file_ext = file.filename.split(".")[-1]
    object_name = f"{prefix}/{uuid4()}.{file_ext}"

    try:
        minio_client.put_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=object_name,
            data=file.file,
            length=-1,
            part_size=10 * 1024 * 1024,
            content_type=file.content_type,
        )

        return f"http://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"
    except S3Error as e:
        print(f"MinIO upload failed: {e}")
        raise
