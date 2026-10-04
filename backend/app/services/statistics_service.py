"""活动统计：基于真实数据聚合（使用既有索引，不做全表扫描）"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DrawStatus
from app.repositories.activity_repository import ActivityRepository
from app.repositories.lottery_repository import LotteryRepository
from app.repositories.participation_repository import ParticipationRepository
from app.repositories.prize_repository import PrizeRepository
from app.repositories.win_record_repository import WinRecordRepository
from app.schemas.statistics import ActivityStaticsResponse, PrizeStatResponse
from app.core.exceptions import NotFoundError


class StatisticsService:
    """运营端活动统计"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.activities = ActivityRepository(db)
        self.records = LotteryRepository(db)
        self.winnings = WinRecordRepository(db)
        self.participations = ParticipationRepository(db)
        self.prizes = PrizeRepository(db)


    async def activity_statistics(self, activity_id: int) -> ActivityStaticsResponse:
        activity = await self.activities.get(activity_id)
        if activity is None:
            raise NotFoundError("活动不存在")
        participant_count = await self.participations.count_by_activity(activity_id)
        draw_count = await self.records.count_by_activity(activity_id)
        win_count = await self.records.count_by_activity(activity_id, DrawStatus.WON)
        no_prize_count = await self.records.count_by_activity(activity_id, DrawStatus.NO_PRIZE)
        win_rate = round(win_count / draw_count, 4) if draw_count > 0 else 0.0

        prize_items, _ = await self.prizes.list_prizes(activity_id=activity_id, page=1, page_size=100)
        prize_stats: list[PrizeStatResponse] = []
        for prize in prize_items:
            drawn_count = await self.records.count_won_by_prize(activity_id, prize.id)
            prize_stats.append(
                PrizeStatResponse(
                    prize_id = prize.id,
                    prize_name = prize.name,
                    prize_type = prize.prize_type,
                    total_stock = prize.total_stock,
                    remain_stock = prize.remain_stock,
                    drawn_count = drawn_count,
                )
            )

        claim_stats = await self.winnings.count_grouped_by_status(activity_id)
        return ActivityStaticsResponse(
            activity_id = activity_id,
            activity_name = activity.name,
            participant_count = participant_count,
            draw_count = draw_count,
            win_count = win_count,
            no_prize_count = no_prize_count,
            win_rate = win_rate,
            prize_stats = prize_stats,
            claim_stats = claim_stats,
        )