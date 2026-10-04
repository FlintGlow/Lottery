"""抽奖记录的 仓储"""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.enums import DrawStatus
from app.models.lottery import DrawRecord, WinRecord
from app.repositories.base import BaseRepository

class LotteryRepository(BaseRepository[DrawRecord]):
    model = DrawRecord

    async def get_by_order_no(self, order_no: int) -> DrawRecord | None:
        return await self.get_by(order_no=order_no)

    async def list_by_user(
            self,
            *,
            user_id: int,
            activity_id: int | None = None,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple[list[DrawRecord], int]:
        conditions = [DrawRecord.user_id == user_id, DrawRecord.is_deleted.is_(False)]
        if activity_id is not None:
            conditions.append(DrawRecord.activity_id == activity_id)

        total = (
            await self.session.execute(
                select(func.count()).select_from(DrawRecord).where(*conditions)
            )
        ).scalar_one()

        stmt = (
            select(DrawRecord)
            .where(*conditions)
            .order_by(DrawRecord.id.desc())
            .offset((page-1)*page_size)
            .limit(page_size)
        )

        rows = (await self.session.execute(stmt)).scalars().all()

        return list(rows), total

    async def win_id_map(self, draw_record_ids:list[int]) -> dict[int, int]:
        if not draw_record_ids:
            return {}
        stmt = (
            select(WinRecord.draw_record_id,WinRecord.id)
            .where(
                WinRecord.draw_record_id.in_(draw_record_ids),
                WinRecord.is_deleted.is_(False),
            )
        )
        rows = (await self.session.execute(stmt)).all()
        return {draw_record_id: win_id for draw_record_id, win_id in rows}

    async def count_by_activity(
            self,
            activity_id: int,
            status: DrawRecord | None = None,
    ) -> int:
        conditions = [DrawRecord.activity_id == activity_id, DrawRecord.is_deleted.is_(False)]
        if status is not None:
            conditions.append(DrawRecord.status == status)
        stmt = select(func.count()).select_from(DrawRecord).where(*conditions)
        return (await self.session.execute(stmt)).scalar_one()

    async def count_won_by_prize(self, activity_id: int, prize_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(DrawRecord)
            .where(
                DrawRecord.activity_id == activity_id,
                DrawRecord.prize_id == prize_id,
                DrawRecord.status == DrawStatus.WON,
                DrawRecord.is_deleted.is_(False),
            )
        )
        return (await self.session.execute(stmt)).scalar_one()