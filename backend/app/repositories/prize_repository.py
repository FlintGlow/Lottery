"""奖品与奖品分类 仓储"""

from __future__ import annotations

from sqlalchemy import func, select, update

from app.models.enums import PrizeStatus
from app.models.lottery import DrawRecord, WinRecord
from app.models.prize import Prize, PrizeCategory
from app.repositories.base import BaseRepository

class PrizeCategoryRepository(BaseRepository[PrizeCategory]):
    model = PrizeCategory

    async def get_by_name(self, name: str) -> PrizeCategory | None:
        return await self.get_by(name=name)

    async def list_categories(self) -> list[PrizeCategory]:
        items, _ = await self.list(
            page =1,
            page_size = 100,
            order_by = PrizeCategory.sort_order,
            descending = False,
        )
        return items

    async def count_prizes(self, category_id: int) -> int:
        """统计分类下未删除的奖品数量。"""
        stmt = (
            select(func.count())
            .select_from(Prize)
            .where(Prize.category_id == category_id, Prize.is_deleted.is_(False))
        )
        return (await self.session.execute(stmt)).scalar_one()


class PrizeRepository(BaseRepository[Prize]):
    model = Prize

    async def list_prizes(
            self,
            *,
            activity_id: int | None = None,
            category_id: int | None = None,
            keyword: str | None = None,
            status: PrizeStatus | None = None,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple[ list[Prize],int ]:
        conditions = [Prize.is_deleted.is_(False)]
        if activity_id is not None:
            conditions.append(Prize.activity_id == activity_id)
        if category_id is not None:
            conditions.append(Prize.category_id == category_id)
        if keyword is not None:
            conditions.append(Prize.name.like(f"%{keyword}%"))
        if status is not None:
            conditions.append(Prize.status == status)

        total = (
            await self.session.execute(
                select(func.count()).select_from(Prize).where(*conditions)
            )
        ).scalar_one()
        stmt = (
            select(Prize)
            .where(*conditions)
            .order_by(Prize.sort_order)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total

    async def count_references(self, prize_id: int) -> int:
        """统计抽奖记录/中奖记录对奖品的引用（决定能否删除）。"""
        lottery_count =(
            await self.session.execute(
                select(func.count())
                .select_from(DrawRecord)
                .where(DrawRecord.prize_id == prize_id)
            )
        ).scalar_one()
        win_count = (
            await self.session.execute(
                select(func.count())
                .select_from(WinRecord)
                .where(WinRecord.prize_id == prize_id)
            )
        ).scalar_one()
        return lottery_count + win_count

    async def adjust_stock(self, prize_id: int, delta: int, expected_version: int) -> bool:
        """乐观锁库存调整：版本号不匹配则返回 False（并发冲突）。"""
        stmt = (
            update(Prize)
            .where(
                Prize.id == prize_id,
                Prize.version == expected_version,
                Prize.is_deleted.is_(False),
            )
            .values(
                total_stock =Prize.total_stock + delta,
                remain_stock =Prize.remain_stock + delta,
                version = Prize.version + 1,
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount == 1

    async def decrement_remain_stock(self, prize_id: int) -> bool:
        """消费端原子扣减剩余库存（防超卖：仅当 remain_stock > 0）。"""
        stmt = (
            update(Prize)
            .where(
                Prize.id == prize_id,
                Prize.remain_stock > 0,
                Prize.is_deleted.is_(False),
            )
            .values(remain_stock = Prize.remain_stock - 1)
        )
        result = await self.session.execute(stmt)
        return result.rowcount == 1




