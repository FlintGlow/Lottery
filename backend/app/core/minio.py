from __future__ import annotations

import io
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from minio import Minio

from app.core.config import get_settings
from app.core.exceptions import BadRequestError

settings = get_settings()

_client: Minio | None = None

_ALLOWED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")


def get_minio() -> Minio:
    """获取 MinIO 客户端（懒加载单例）。"""
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )

    return _client


async def ensure_bucket() -> None:
    """启动时确保 bucket 存在并开放公开读（开发环境配置）。"""
    client = get_minio()
    bucket = settings.MINIO_BUCKET

    def _ensure() -> None:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket}/*"],
                }
            ],
        }
        client.set_bucket_policy(bucket, json.dumps(policy))

    await asyncio.to_thread(_ensure)



async def upload_image(file: UploadFile, prefix: str = "prizes") -> str:
    """上传图片到 MinIO，返回公开访问 URL。

        校验内容类型与大小；对象键按 奖品/年月/UUID 组织。
    """
    content = await file.read()
    if not content:
        raise BadRequestError("文件内容为空")
    max_size = settings.MINIO_UPLOAD_MAX_SIZE
    if len(content) > max_size:
        raise BadRequestError(f"图片大小不能超过{max_size // (1024 * 1024)}MB")

    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise BadRequestError("仅支持上传图片文件")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise BadRequestError(f"仅支持上传以下图片格式: {','.join(_ALLOWED_EXTENSIONS)}")
    key = f"{prefix}/{datetime.now():%Y%m}/{uuid.uuid4().hex}{ext}"


    def _put() -> None:
        get_minio().put_object(
            settings.MINIO_BUCKET,
            key,
            io.BytesIO(content),
            length=len(content),
            content_type=content_type,
        )

    await asyncio.to_thread(_put)
    return f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET}/{key}"