"""哈希密码与 JWT令牌"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import uuid
import bcrypt
import jwt

from app.core.config import get_settings
from app.core.exceptions import TokenError
from app.core.exceptions import BadRequestError

settings = get_settings()
BCRYPT_ROUNDS = 12
MAX_PASSWORD_BYTES = 72

def hash_password(password: str) -> str:

    raw = password.encode("utf-8")
    if len(raw) > MAX_PASSWORD_BYTES:
        raise BadRequestError(
            f"密码过长：UTF-8编码后不得超过{MAX_PASSWORD_BYTES} 字节"
        )
    """BCrypt 哈希密码。"""
    return bcrypt.hashpw(
        raw,
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS),
    ).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验密码，哈希格式非法时返回False"""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except ValueError:
        return False


def create_access_token(subject: str, extra: dict |None = None) -> tuple[str, int]:
    """生成 Access Token，返回（token, 有效期）"""
    delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(subject, "access",delta, extra), int(delta.total_seconds())


def create_refresh_token(subject: str) -> tuple[str, int]:
    """生成 Refresh Token，返回（token, 有效期）"""
    delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(subject, "refresh", delta), int(delta.total_seconds())

def decode_token(token: str) -> dict:
    """解码并校验令牌，失败抛 TokenError。"""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.PyJWTError as exc:
        raise TokenError() from exc


def _create_token(
        subject: str,
        token_type: str,
        expire_delta: timedelta,
        extra: dict |None = None
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expire_delta,
        "jti": str(uuid.uuid4()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
