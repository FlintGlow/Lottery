"""认证业务： 注册、登录、刷新、登出、个人资料"""

from __future__ import annotations

from datetime import datetime
import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppError, ConflictError, ForbiddenError, TooManyRequestsError, UnauthorizedError
from app.core.redis import get_redis
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password, hash_password
from app.models.enums import UserStatus
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest, TokenPair
from app.schemas.user import ChangePasswordResponse, UserUpdateMe
from app.models import User

settings = get_settings()
logger = logging.getLogger(__name__)

DEFAULT_ROLE_CODE = "user"
LOGIN_RATE_LIMIT = 10       # 每窗口允许的最大登录尝试次数
LOGIN_RATE_WINDOW = 60      # 窗口时长（秒）


class AuthService:
    """用户认证与个人资料服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)

    async def register(self, data:RegisterRequest, ip:str | None = None) -> TokenPair:
        """用户注册会自动登录，返回令牌对"""
        if await self.users.get_by_username(data.username):
            raise ConflictError("用户名已存在")
        if await self.users.get_by_phone(data.phone_number):
            raise ConflictError("手机号已注册")

        default_role = await self.roles.get_by_code(DEFAULT_ROLE_CODE)
        if default_role is None:
            raise AppError("默认角色未初始化，请先执行数据库初始化/迁移",code=50000, status_code=500)

        user = User(
            username=data.username,
            password_hash=hash_password(data.password),
            phone_number=data.phone_number,
            roles=[default_role],
        )
        self.db.add(user)
        try:
            await self.db.flush()
        except IntegrityError as exc:
            #并发注册时唯一约束兜底
            raise ConflictError("用户名、手机号已被占用") from exc

        await self.db.commit()
        logger.info("注册成功 user_id=%s ip=%s", user.id, ip)
        return await self._issue_tokens(user)

    async def login(self, data:LoginRequest, ip: str | None = None) -> TokenPair:
        """登录： 支持用户名/手机号， 带Redis限流"""
        await self._check_login_rate(ip or "", data.account)

        user = await self.users.get_by_username(data.account) or await self.users.get_by_phone(data.account)
        if user is  None or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("账号或密码错误")
        if user.status != UserStatus.ACTIVE:
            raise ForbiddenError("账号被禁用")

        user.last_login_at = datetime.now()
        await self.db.flush()
        await self.db.commit()
        logger.info("登录成功 user_id=%s ip=%s", user.id, ip)
        return await self._issue_tokens(user)

    async def refresh(self, data:RefreshRequest) -> TokenPair:
        """刷新 Access_Token(Refresh Token 不轮换，注销通过黑名单生效)"""
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("无效的刷新令牌")
        await self._ensure_token_active(payload)

        user = await self.users.get(int(payload["sub"]))
        if user is None or user.status != UserStatus.ACTIVE:
            raise UnauthorizedError("用户不存在或已被禁用")

        access_token, expires_in = create_access_token(str(user.id), extra={"roles": [role.code for role in user.roles]})
        return TokenPair(access_token=access_token, refresh_token=data.refresh_token,expires_in=expires_in)

    async def logout(self, data:LogoutRequest) -> None:
        """将令牌加入黑名单直至过期"""
        payload = decode_token(data.token)
        await self._blacklist_token(payload)

    async def update_profile(self, user:User, data: UserUpdateMe) -> User:
        """更新个人资料"""
        if data.name is not None and data.name != user.username:
            existing = await self.users.get_by_username(data.name)
            if existing is not None and existing.id != user.id:
                raise ConflictError("用户名已被存在")
            user.username = data.name

        if data.phone_number is not None and data.phone_number != user.phone_number:
            existing = await self.users.get_by_phone(data.phone_number)
            if existing is not None and existing.id != user.id:
                raise ConflictError("手机号已被注册")
            user.phone_number = data.phone_number

        if data.avatar_url is not None:
            user.avatar_url = data.avatar_url
        await self.db.flush()
        await self.db.commit()
        return user

    async def change_password(self, user:User, data: ChangePasswordResponse, ip: str | None = None) -> None:
        """修改密码： 检验原密码后写入新哈希"""
        if not verify_password(data.old_password, user.password_hash):
            raise UnauthorizedError("原密码错误")
        user.password_hash = hash_password(data.new_password)
        await self.db.flush()
        await self.db.commit()
        logger.warning("修改密码成功 user_id=%s ip=%s", user.id, ip)

    async def _issue_tokens(self, user:User) -> TokenPair:
        access_token, expires_in = create_access_token(str(user.id),extra={"roles": [role.code for role in user.roles]})

        refresh_token, _ = create_refresh_token(str(user.id))

        return TokenPair(access_token=access_token, refresh_token=refresh_token, expires_in=expires_in)


    async def _check_login_rate(self, ip: str, account: str) -> None:
        redis = await get_redis()
        key = f"auth:login:rate:{ip}:{account}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, LOGIN_RATE_WINDOW)
        if count > LOGIN_RATE_LIMIT:
            raise TooManyRequestsError()

    async def _ensure_token_active(self, payload: dict) -> None:
        radis = await get_redis()
        if await radis.exists(f"auth:blacklist:{payload['jti']}"):
            raise UnauthorizedError("令牌已失效")

    async def _blacklist_token(self, payload: dict) -> None:
        redis = await get_redis()
        ttl = int(payload["exp"]) - int(datetime.now().timestamp())
        if ttl > 0:
            await redis.set(f"auth:blacklist:{payload['jti']}", "1", ex=ttl)