"""奖品与奖品分类 Schema"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, model_validator

from app.models.enums import PrizeType, PrizeStatus

# ==================== 奖品分类 Schema ====================

class PrizeCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64, description="分类名称")
    description: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0, ge=0)


class PrizeCategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=64, description="分类名称")
    description: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0, ge=0)
    status: PrizeStatus | None = None

class PrizeCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    sort_order: int
    status: PrizeStatus
    created_at: datetime


# ==================== 奖品 Schema====================


class PrizeCreate(BaseModel):
    activity_id: int = Field(description="所属活动ID")
    category_id: int | None = Field(default=None, description="分类ID")
    name: str = Field(min_length=1, max_length=128, description="奖品名称")
    prize_type: PrizeType = Field(default=PrizeType.PHYSICAL, description="奖品类型")
    prize_level: str | None = Field(default=None, max_length=32, description="奖品等级")
    description: str | None = Field(default=None, max_length=2000, description="奖品描述")
    total_stock: int = Field(default=0, ge=0, description="总库存")
    weight: int = Field(default=0, ge=0, description="中奖权重(0=不参与)")
    daily_limit: int = Field(
        default=0, ge=0, description="每日中出上限(0=不限)，仅管理端与运营可见"
    )
    img_url: str | None = Field(default=None, max_length=255, description="奖品图片URL")
    sort_order: int = Field(default=0, ge=0)


class PrizeUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=2000)
    prize_type: PrizeType | None = Field(default=None)
    prize_level: str | None = Field(default=None, max_length=32)
    weight: int | None = Field(default=None, ge=0)
    daily_limit: int | None = Field(default=None, ge=0, description="每日中出上限(0=不限)")
    img_url: str | None = Field(default=None, max_length=255)
    sort_order: int | None = Field(default=None, ge=0)
    status: PrizeStatus | None = Field(default=None)


class PrizeStockAdjust(BaseModel):
    version: int = Field(ge=0, description="乐观锁版本号（来自当前奖品数据）")
    delta: int = Field(description="库存调整量：正数增加，负数减少")


class PrizesResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    activity_id: int
    category_id: int | None
    # 由 Service 在 model_validate 之后填充（Prize 实体本身没有该属性），
    # 因此必须给默认值，否则 model_validate 会直接抛 ValidationError。
    category_name: str | None = None
    name: str
    description: str | None
    prize_type: PrizeType
    prize_level: str | None
    total_stock: int
    remain_stock: int
    weight: int
    daily_limit: int = Field(description="每日中出上限(0=不限)，仅管理端与运营可见")
    img_url: str | None
    sort_order: int
    version: int
    status: PrizeStatus
    created_at: datetime
    updated_at: datetime


class PrizePublishResponse(BaseModel):
    """用户端可见的奖品信息。

    刻意不包含 weight / total_stock / daily_limit / version 等运营参数：
    每日中出上限属于运营配置，只对管理端与运营人员可见。
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    name: str
    description: str | None
    img_url: str | None
    prize_level: str | None
    remain_stock: int
    sort_order: int
    prize_type: PrizeType
