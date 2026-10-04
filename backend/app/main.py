"""FastApi 应用入口： 注册中间件、异常处理与各模块Router"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import(
    activities,
    auth,
    files,
    lottery,
    operations,
    prizes,
    rewards,
    roles,
    statustics,
    users,
    winnings,
)
from app.api.errors import register_exception_handlers
from app.core.config import get_settings
from app.core.minio import ensure_bucket
from app.core.rabbitmq import close_rabbitmq
from app.core.redis import close_redis
from app.middleware.request_log import RequestLogMiddleware

settings = get_settings()
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await ensure_bucket()
    except Exception:
        logger.exception("MinIO初始化失败,图片上传功能不可用")
    yield
    await close_redis()
    await close_rabbitmq()

app = FastAPI(
    title = f"{settings.APP_NAME}API",
    version = "0.2.0",
    description = "幸运抽奖系统",
    docs_url = f"{settings.API_V1_PREFIX}/docs",
    openapi_url = f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan = lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RequestLogMiddleware)

register_exception_handlers(app)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(roles.router, prefix=settings.API_V1_PREFIX)
app.include_router(activities.public_router, prefix=settings.API_V1_PREFIX)
app.include_router(activities.admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(prizes.public_router, prefix=settings.API_V1_PREFIX)
app.include_router(prizes.admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(prizes.category_admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(prizes.files_router, prefix=settings.API_V1_PREFIX)
app.include_router(lottery.router, prefix=settings.API_V1_PREFIX)
app.include_router(winnings.router, prefix=settings.API_V1_PREFIX)
app.include_router(winnings.admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(rewards.admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(statustics.admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(files.router, prefix=settings.API_V1_PREFIX)
app.include_router(operations.router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
    }

