"""活动参与资格的 仓储"""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.participation import ActivityParticipation
from app.repositories.base import BaseRepository


class ParticipationRepository(BaseRepository[ActivityParticipation]):
    model = ActivityParticipation

    async def exists(self, activity_id: int, phone_number: str) -> bool:
        return await self.get_by(activity_id=activity_id, phone_number=phone_number) is not None

    async def count_by_activity(self, activity_id:int) -> int:
        stmt = (
            select(func.count())
            .select_from(ActivityParticipation)
            .where(ActivityParticipation.activity_id == activity_id)
        )

        return (await self.session.execute(stmt)).scalar_one()