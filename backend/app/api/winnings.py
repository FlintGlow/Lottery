"""中奖记录接口： 用户端我的中奖/领奖 + 运营端管理"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession


from app.api.deps import require_roles, get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.enums import RedemptionStatus
from app.schemas.common import ApiResponse, PaginatedResponse, PageParams, ok
from app.schemas.winnings import RedemptionSubmitRequest, WinRecordStatusUpdate, WinRecordResponse
from app.services.claim_service import ClaimService
from app.services.winnings_service import WinningsService

router = APIRouter(prefix="/winnings", tags=["中奖记录"])
admin_router = APIRouter(prefix="/admin/winnings", tags=["运营-中奖记录"])


@router.get("/me", response_model=ApiResponse[PaginatedResponse[WinRecordResponse]])
async def my_winnings(
        params: PageParams = Depends(),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[WinRecordResponse]]:
    """我的中奖记录"""
    items, total = await WinningsService(db).list_my(
        current_user,
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


@router.get("/me/{win_id}", response_model=ApiResponse[WinRecordResponse])
async def my_winning(
        win_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[WinRecordResponse]:
    """我的中奖详情"""
    return ok(await WinningsService(db).get_my(current_user, win_id))


@router.post("/{win_id}/claim", response_model=ApiResponse[WinRecordResponse])
async def submit_claim(
        win_id: int,
        data: RedemptionSubmitRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[WinRecordResponse]:
    """提交领奖信息"""
    await ClaimService(db).submit(current_user, win_id, data)
    return ok(
        await WinningsService(db).get_my(current_user, win_id),
        "领奖信息已提交",
    )


@admin_router.get("", response_model=ApiResponse[PaginatedResponse[WinRecordResponse]])
async def list_winnings(
        params: PageParams = Depends(),
        activity_id: int | None = None,
        status: RedemptionStatus | None = None,
        keyword: str | None = None,
        _: User = Depends(require_roles("admin","operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[WinRecordResponse]]:
    """运营端中奖记录列表"""
    items, total = await WinningsService(db).list_for_operations(
        activity_id = activity_id,
        status=status.value if status else None,
        keyword=keyword,
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

@admin_router.patch("/{win_id}/status", response_model=ApiResponse[WinRecordResponse])
async def update_winnings_status(
        win_id: int,
        data: WinRecordStatusUpdate,
        operator: User = Depends(require_roles("admin","operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[WinRecordResponse]:
    """运营端状态流转"""
    return ok(await WinningsService(db).update_status(operator, win_id, data), "状态已更新")