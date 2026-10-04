"""中奖记录与领奖 Schema"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import RedemptionStatus, PrizeType


class RedemptionSubmitRequest(BaseModel):
    """领奖信息提交：实物奖需姓名/手机号/地址，虚拟奖仅需手机号（服务层按类型校验）。"""

    recipient_name: str | None = Field(default=None, max_length=64, description="收货姓名")
    recipient_phone: str | None = Field(default=None, pattern=r'^1[3-9]\d{9}$', description="领奖手机号")
    recipient_address: str | None =Field(default=None, max_length=255, description="收货地址")

class WinRecordResponse(BaseModel):

    id: int
    order_no: str
    activity_id: int
    activity_name: str | None
    username: str | None
    prize_id: int
    prize_name: str
    prize_image: str | None
    prize_type: PrizeType
    redemption_status: RedemptionStatus
    recipient_name: str |None
    recipient_phone: str | None
    recipient_address: str | None
    redemption_at: datetime | None
    processed_by: int | None
    processed_at: datetime | None
    process_remark: str | None
    created_at: datetime


class WinRecordStatusUpdate(BaseModel):
    """运营端状态变更（仅允许状态机内的合法流转）。"""

    status: RedemptionStatus
    remark: str | None = Field(None, max_length=255)


