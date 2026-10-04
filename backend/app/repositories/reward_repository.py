"""补发记录 仓储"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import aliased

from app.models.prize import Prize
from app.models.reward import ManualReward
from app.models.user import User
from app.repositories.base import BaseRepository


class ManualRewardRepository(BaseRepository[ManualReward]):
    model = ManualReward

    async def list_rewards(
            self,
            *,
            operator: str | None = None,
            activity_id: int | None = None,
            user_id: int | None = None,
            username: str | None = None,
            phone_number: str | None = None,
            prize_id: int | None = None,
            keyword: str | None = None,
            status: str | None = None,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple[list[ManualReward], int]:
        operator_user = aliased(User)
        conditions = [ManualReward.is_deleted.is_(False)]
        if status:
            conditions.append(ManualReward.status == status)
        if activity_id is not None:
            conditions.append(ManualReward.activity_id == activity_id)
        if user_id is not None:
            conditions.append(ManualReward.user_id == user_id)
        if prize_id is not None:
            conditions.append(ManualReward.prize_id == prize_id)
        if start_time is not None:
            conditions.append(ManualReward.created_at >= start_time)
        if end_time is not None:
            conditions.append(ManualReward.created_at <= end_time)
        if username:
            conditions.append(User.username.like(f"%{username}%"))
        if phone_number:
            conditions.append(User.phone_number == phone_number)
        if operator:
            like = f"%{operator}%"
            conditions.append(
                or_(
                    ManualReward.operator_name.like(like),
                    operator_user.username.like(like),
                )
            )
        if keyword:
            like = f"%{keyword}%"
            conditions.append(
                or_(
                    User.username.like(like),
                    User.phone_number.like(like),
                    Prize.name.like(like),
                    ManualReward.reason.like(like),
                )
            )

        def _build(columns):
            return (
                select(columns)
                .select_from(ManualReward)
                .join(User, User.id == ManualReward.user_id)
                .join(Prize, Prize.id == ManualReward.prize_id)
                .outerjoin(operator_user, operator_user.id == ManualReward.user_id)
                .where(*conditions)
            )

        total = (await self.session.execute(_build(func.count()))).scalar_one()
        stmt = (
            _build(ManualReward)
            .order_by(ManualReward.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows),total