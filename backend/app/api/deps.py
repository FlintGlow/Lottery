"""API 依赖：当前用户、角色校验"""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.redis import get_redis
from app.core.security import decode_token
from app.core.database import get_db

from app.models.user import User
from app.models.enums import UserStatus, RoleStatus
from app.repositories.user_repository import UserRepository

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl = f"{settings.API_V1_PREFIX}/auth/login",
)


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
) -> User:
    """解析 Access Token 并加载当前用户"""
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise UnauthorizedError("令牌类型错误")

    redis = await get_redis()
    if await redis.exists(f"auth:blacklist:{payload['jti']}"):
        raise UnauthorizedError("令牌已失效")

    user = await UserRepository(db).get(int(payload["sub"]))
    if user is None or user.status != UserStatus.ACTIVE:
        raise UnauthorizedError("用户不存在或已被禁用")
    return user


def require_roles(*roles: str):
    """角色权限依赖工厂： 用户需拥有指定角色之一"""

    async def _checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_codes = {role.code for role in current_user.roles if role.status == RoleStatus.ENABLED and not role.is_deleted}
        if not user_role_codes.intersection(roles):
            raise ForbiddenError()
        return current_user

    return _checker