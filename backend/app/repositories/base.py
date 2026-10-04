"""通用仓储基类。

Repository 层只封装数据访问，Service 层不直接书写 SQLAlchemy 查询。
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """通用单表 CRUD"""

    model:type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, obj_id: int) -> ModelType | None:
        """按主键获取"""
        obj = await self.session.get(self.model, obj_id)
        if obj is None or (hasattr(obj, "is_deleted") and obj.is_deleted):
            return None
        return obj

    async def get_by(self, **filters: Any) -> ModelType | None:
        """按字段条件获取单条。"""
        stmt = self._append_soft_delete(select(self.model).filter_by(**filters))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists(self, **filters: Any) -> bool:
        """判断记录是否存在"""
        return await self.get_by(**filters) is not None

    async def list(
            self,
            *,
            page: int = 1,
            page_size: int = 20,
            order_by: Any | None = None,
            descending: bool = True,
            **filters: Any,
    ) -> tuple[list[ModelType], int]:
        """分页查询，返回（记录列表，总数）"""
        base = self._append_soft_delete(select(self.model).filter_by(**filters))
        total = (
            await self.session.execute(
                select(func.count()).select_from(base.subquery())
            )
        ).scalar_one()

        stmt = base
        if order_by is not None:
            stmt = stmt.order_by(order_by.desc() if descending else order_by.asc())
        stmt = stmt.offset((page - 1)*page_size).limit(page_size)
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total

    async def add(self, obj: ModelType) -> ModelType:
        """新增并 flush，随后回读服务端默认值（id/时间戳），避免过期属性。"""
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    def _append_soft_delete(self, stmt: Any) -> Any:
        """模型含 is_deleted 时默认过滤已删除数据"""
        if hasattr(self.model, "is_deleted"):
            return stmt.where(self.model.is_deleted.is_(False))
        return stmt