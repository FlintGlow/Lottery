"""活动统计 Schema"""

from __future__ import annotations

from pydantic import BaseModel


class PrizeStatResponse(BaseModel):
    prize_id: int
    prize_name: str
    prize_type: str
    total_stock: int
    remain_stock: int
    drawn_count: int


class ActivityStaticsResponse(BaseModel):
    activity_id: int
    activity_name: str
    created_by_name: str | None = None
    participant_count: int
    draw_count: int
    win_count: int
    no_prize_count: int
    win_rate: float
    prize_stats: list[PrizeStatResponse] = []
    claim_stats: dict[str, int] = {}
