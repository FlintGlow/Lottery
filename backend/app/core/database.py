from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, Boolean, DateTime, func, text

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=20,
    max_overflow=10,
)
AsyncSessionLocal = async_sessionmaker(
    bind = engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""

    # 异步 + server_default 场景：flush 时立即回读默认值，
    __mapper_args__ = {"eager_defaults": True}

class IdMixin:
    """统一主键：BIGINT 自增"""
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主键ID",
    )


class TimestampMixin:
    """统一时间戳"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="更新时间",
    )


class SoftDeleteMixin:
    """统一软删除"""

    is_deleted:Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
        index=True,
        comment="软删除标记：0-正常 1-已删除",
    )



async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """ FastAPI依赖： 提供请求级会话，事务由Service层显示提交。

        如果请求过程中发生异常，这里负责回滚。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
