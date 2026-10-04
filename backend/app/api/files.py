"""文件接口： 任意登录用户可上传（头像等）"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_current_user
from app.core.minio import upload_image
from app.models.user import User
from app.schemas.common import ApiResponse, ok

router = APIRouter(prefix="/files", tags=["文件"])

@router.post("/images", response_model=ApiResponse[dict], status_code=201)
async def upload_user_image(
        file: UploadFile = File(...),
        _:User = Depends(get_current_user),
) -> ApiResponse[dict]:
    """上传图片，用于头像，返回公开URL"""
    url = await upload_image(file, prefix="avatars")
    return ok({"url": url}, "上传成功")