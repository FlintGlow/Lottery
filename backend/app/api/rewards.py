"""补发接口（运营端，admin/operator）。"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_roles
from app.models.enums import ManualRewardStatus
from app.models.user import User
from app.schemas.common import ApiResponse, PageParams, PaginatedResponse, ok
from app.schemas.reward import ManualRewardCreate, ManualRewardResponse, ManualRewardStatusUpdate
from app.services.reward_service import RewardService

admin_router = APIRouter(prefix="/admin/rewards", tags=["运营-补发"])


@admin_router.get("", response_model=ApiResponse[PaginatedResponse[ManualRewardResponse]])
async def list_rewards(
        params: PageParams = Depends(),
        operator: str | None = None,
        activity_id: int | None = None,
        user_id: int | None = None,
        username: str | None = None,
        phone_number: str | None = None,
        prize_id: int | None = None,
        keywords: str | None = None,
        status: ManualRewardStatus | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        _:User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[ManualRewardResponse]]:
    """补发记录列表（操作人/活动/用户/手机号/奖品/状态/时间 多条件搜索）。"""
    items, total = await RewardService(db).list(
        operator = operator,
        activity_id = activity_id,
        user_id = user_id,
        username = username,
        phone_number = phone_number,
        prize_id = prize_id,
        keyword = keywords,
        status = status.value if status else None,
        start_time = start_time,
        end_time = end_time,
        page = params.page,
        page_size = params.page_size,
    )

    return ok(
        PaginatedResponse(
            items = items,
            total = total,
            page = params.page,
            page_size = params.page_size,
        )
    )


@admin_router.post("/manual", response_model=ApiResponse[ManualRewardResponse], status_code=201)
async def create_manual_reward(
        data: ManualRewardCreate,
        operator: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[ManualRewardResponse]:
    """人工补发奖品（不修改原中奖记录，保留操作审计）"""
    return ok(await RewardService(db).create(operator, data), "补发记录已创建")


@admin_router.patch("/{reward_id}/status", response_model=ApiResponse[ManualRewardResponse])
async def update_reward_status(
        reward_id: int,
        data: ManualRewardStatusUpdate,
        operator: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[ManualRewardResponse]:
    """补发状态变更（代发放 -> 已发放/已取消）"""
    return ok(
        await RewardService(db).update_status(operator, reward_id, data),
        "状态已更新",
    )