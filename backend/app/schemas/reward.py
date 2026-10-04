"""补发记录 Schema"""

from __future__ import annotations

from pydantic import BaseModel, Field

from datetime import datetime

from app.models.enums import ManualRewardStatus


class ManualRewardCreate(BaseModel):
    user_id: int = Field(description="补发用户ID")
    prize_id: int = Field(description="补发奖品")
    draw_record_id: int | None = Field(default=None, description="关联的抽奖记录")
    reason: str = Field(min_length=1, max_length=255, description="补发原因")
    remark: str | None = Field(default=None, max_length=255, description="备注")


class ManualRewardResponse(BaseModel):
    id: int
    user_id: int
    user_name: str | None
    phone_number: str | None
    activity_id: int
    activity_name: str | None
    prize_id: int
    prize_name: str | None
    prize_type: str | None
    draw_record_id: int | None
    reason: str
    status: ManualRewardStatus
    operator_id: int | None
    operator_name: str | None
    operated_at: datetime | None
    remark: str | None
    created_at: datetime


class ManualRewardStatusUpdate(BaseModel):
    status: ManualRewardStatus
    remark: str | None = Field(default=None, max_length=255)