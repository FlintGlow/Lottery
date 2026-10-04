"""中奖记录 仓储。"""

from __future__ import annotations

from sqlalchemy import select, func, or_

from app.models.lottery import WinRecord
from app.models.user import User
from app.repositories.base import BaseRepository


class WinRecordRepository(BaseRepository[WinRecord]):
    model = WinRecord

    async def get_by_draw_record(self, draw_record_id: int) -> WinRecord | None:
        return await self.get_by(draw_record_id=draw_record_id)

    async def list_by_user(
            self,
            *,
            user_id: int,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple[list[WinRecord], int]:
        conditions = [WinRecord.user_id == user_id, WinRecord.is_deleted.is_(False)]
        total = (
            await self.session.execute(
                select(func.count()).select_from(WinRecord).where(*conditions)
            )
        ).scalar_one()
        stmt = (
            select(WinRecord)
            .where(*conditions)
            .order_by(WinRecord.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total

    async def list_for_operations(
            self,
            *,
            activity_id: int | None = None,
            status: str | None = None,
            keyword: str | None = None,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple[list[WinRecord], int]:
        conditions = [WinRecord.is_deleted.is_(False)]
        if activity_id is not None:
            conditions.append(WinRecord.activity_id == activity_id)
        if status:
            conditions.append(WinRecord.redemption_status == status)
        if keyword:
            like = f"%{keyword}%"
            conditions.append(
                or_(
                    User.username.like(like),
                    User.phone_number.like(like),
                )
            )
        total = (
            await self.session.execute(
                select(func.count())
                .select_from(WinRecord)
                .join(User, User.id == WinRecord.user_id)
                .where(*conditions)
            )
        ).scalar_one()
        stmt = (
            select(WinRecord)
            .join(User, User.id == WinRecord.user_id)
            .where(*conditions)
            .order_by(WinRecord.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total

    async def count_grouped_by_status(self, activity_id: int) -> dict[str, int]:
        """按领奖状态聚合（走 win_records 活动维度索引）。"""
        stmt = (
            select(WinRecord.redemption_status, func.count())
            .where(WinRecord.activity_id == activity_id, WinRecord.is_deleted.is_(False))
            .group_by(WinRecord.redemption_status)
        )
        rows = (await self.session.execute(stmt)).all()
        result: dict[str, int] = {}
        for status, count in rows:
            value = status.value if hasattr(status, "value") else status
            result[str(value)] = count
        return result

