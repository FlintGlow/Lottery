from __future__ import annotations

from redis.asyncio import Redis

from app.core.config import get_settings


settings = get_settings()

_redis_client: Redis | None = None


async def get_redis() -> Redis:
    """获取连接"""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf-8",
        )

    return _redis_client


async def close_redis() -> None:
    """应用关闭时释放连接池"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None

