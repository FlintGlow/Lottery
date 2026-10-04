"""活动仓储"""

from __future__ import annotations

from sqlalchemy import func, or_, select, update
from datetime import datetime

from app.models.activity import Activity
from app.models.prize import Prize
from app.repositories.base import BaseRepository
from app.models.enums import ActivityStatus


class ActivityRepository(BaseRepository[Activity]):
    model = Activity

    async def list_activities(
            self,
            *,
            page: int = 1,
            page_size: int = 20,
            keyword: str | None = None,
            status: str | None = None,
            exclude_status: list[str] | None = None
    ) -> tuple[list[Activity], int]:
        """活动分页列表，支持关键字与状态筛选。"""
        conditions = [Activity.is_deleted.is_(False)]
        if keyword:
            like = f"%{keyword}%"
            conditions.append(
                or_(
                    Activity.name.like(like),
                    Activity.description.like(like)
                )
            )
        if status:
            conditions.append(Activity.status == status)
        if exclude_status:
            conditions.append(Activity.status.notin_(exclude_status))

        total = (
            await self.session.execute(
                select(func.count()).select_from(Activity).where(*conditions)
            )
        ).scalar_one()
        stmt = (
            select(Activity)
            .where(*conditions)
            .order_by(Activity.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total


    async def advance_statuses(self, now: datetime) -> tuple[int, int]:
        """根据当前时间批量推进活动状态"""

        #1.已到结束时间的进行中/暂停活动 -> 已结束
        end_result = await self.session.execute(
            update(Activity)
            .where(
                Activity.is_deleted.is_(False),
                Activity.status.in_(
                    [
                        ActivityStatus.ONGOING,
                        ActivityStatus.PAUSED,
                    ]
                ),
                Activity.end_time.is_not(None),
                Activity.end_time <= now,
            )
            .values(status=ActivityStatus.ENDED)
        )

        # 2.待开始但结束时间已到的活动 -> 已结束
        expired_pending_result = await self.session.execute(
            update(Activity)
            .where(
                Activity.is_deleted.is_(False),
                Activity.status == ActivityStatus.PENDING,
                Activity.end_time.is_not(None),
                Activity.end_time <= now,
            )
            .values(status=ActivityStatus.ENDED)
        )

        # 3. 到达开始时间且尚未结束的活动 -> 进行中
        ongoing_result = await self.session.execute(
            update(Activity)
            .where(
                Activity.is_deleted.is_(False),
                Activity.status == ActivityStatus.PENDING,
                Activity.start_time <= now,
                or_(
                    Activity.end_time >= now,
                    Activity.end_time.is_(None),
                )
            )
            .values(status=ActivityStatus.ONGOING)
        )

        await self.session.commit()

        ended_count =(
            (end_result.rowcount or 0) +(expired_pending_result.rowcount or 0)
        )
        ongoing_count =ongoing_result.rowcount or 0

        return ended_count, ongoing_count

    async def count_prizes(self, activity_id: int) -> int:
        """统计活动下未删除的奖品数量"""
        stmt = (
            select(func.count())
            .select_from(Prize)
            .where(
                Prize.activity_id == activity_id,
                Prize.is_deleted.is_(False)
            )
        )
        return (await self.session.execute(stmt)).scalar_one()