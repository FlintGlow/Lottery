"""抽奖相关 Schema"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import DrawStatus


class DrawResultOut(BaseModel):
    """抽奖受理结果：异步落库，前端凭 order_no 轮询。"""

    order_no: str
    status: str = "processing"
    message: str = "抽奖请求已受理，结果处理中"


class LotteryRecordResponse(BaseModel):
    order_no: str
    activity_id: int
    prize_id: int | None
    status: DrawStatus
    result_json: dict | None
    error_message: str | None
    created_at: datetime
    win_id: int | None = None