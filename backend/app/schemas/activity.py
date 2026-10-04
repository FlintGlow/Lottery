"""活动相关的Schema"""

from __future__ import annotations

from datetime import datetime


from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ActivityStatus


class ActivityRuleConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    need_phone: bool = False
    need_name: bool = False
    announcement: str | None = None


class ActivityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128, description='活动名称')
    description: str | None = Field(None, max_length=2000, description="活动描述")
    cover_url: str | None = Field(None, max_length=255, description="封面图(MinIO)")
    start_time: datetime  = Field(description="开始时间")
    end_time: datetime  = Field(description="结束时间")
    daily_draw_limit: int = Field(0, ge=0, description="每人每日抽奖上限(0=不限)")
    total_draw_limit: int = Field(0, ge=0, description="活动总抽奖上限(0=不限)")
    rule_config: ActivityRuleConfig | None = Field(None, description="扩展规则配置")


    @model_validator(mode='after')
    def validate_time(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("结束时间必须晚于开始时间")

        return self


class ActivityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(None, max_length=2000)
    cover_url: str | None = Field(None, max_length=255)
    start_time: datetime | None = None
    end_time: datetime | None = None
    daily_draw_limit: int | None = Field(None, ge=0)
    total_draw_limit: int | None = Field(None, ge=0)
    rule_config: ActivityRuleConfig | None = None

    @model_validator(mode='after')
    def validate_time(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("结束时间必须晚于开始时间")
        return self


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    cover_url: str | None
    start_time: datetime
    end_time: datetime
    status: ActivityStatus
    daily_draw_limit: int
    total_draw_limit: int
    rule_config: dict | None
    created_by: int | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ActivityDetailResponse(ActivityResponse):
    prize_count: int = 0

