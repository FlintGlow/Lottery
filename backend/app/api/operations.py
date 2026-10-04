"""运营端接口：运营人员可访问（admin/operator）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.enums import UserStatus
from app.models.user import User
from app.schemas.common import ApiResponse, PageParams, PaginatedResponse, ok
from app.schemas.prize import PrizesResponse
from app.schemas.user import UserResponse
from app.services.prize_service import PrizeService
from app.services.user_service import UserService

router = APIRouter(prefix="/operations", tags=["运营"])


@router.get("/users", response_model=ApiResponse[PaginatedResponse[UserResponse]])
async def list_operation_users(
        params: PageParams = Depends(),
        keyword: str | None = None,
        status: UserStatus | None = None,
        _: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[UserResponse]]:
    """运营端用户查看"""
    items, total = await UserService(db).list_users(
        page = params.page,
        page_size = params.page_size,
        keyword = keyword,
        status = status.value if status else None,
    )
    return ok(
        PaginatedResponse(
            items = items,
            total = total,
            page = params.page,
            page_size = params.page_size,
        )
    )

@router.get("/prizes", response_model=ApiResponse[PaginatedResponse[PrizesResponse]])
async def list_operation_prizes(
        params: PageParams = Depends(),
        activity_id: int | None = None,
        keyword: str | None = None,
        _: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[PrizesResponse]]:
    """运营端奖品查询（用于补发选择等）。"""
    items, total = await PrizeService(db).list_prizes(
        activity_id = activity_id,
        keyword = keyword,
        page = params.page,
        page_size= params.page_size,
    )
    return ok(
        PaginatedResponse(
            items = items,
            total = total,
            page = params.page,
            page_size = params.page_size,
        )
    )
