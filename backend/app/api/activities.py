"""活动接口：用户端公开查询 + 管理端 CRUD 与状态机。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.api.deps import require_roles

from app.models.user import User
from app.schemas.common import ApiResponse, ok, PageParams, PaginatedResponse
from app.schemas.activity import ActivityCreate, ActivityUpdate, ActivityResponse, ActivityDetailResponse
from app.models.enums import ActivityStatus
from app.services.activity_service import ActivityService

public_router = APIRouter(prefix="/activities", tags=["活动"])
admin_router = APIRouter(prefix="/admin/activities", tags=["管理活动"])

def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None

@public_router.get("", response_model=ApiResponse[list[ActivityResponse]])
async def list_public_activities(
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[ActivityResponse]]:
    return ok(await ActivityService(db).list_public())

@public_router.get("/{activity_id}", response_model=ApiResponse[ActivityDetailResponse])
async def get_public_activity(
        activity_id: int,
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActivityDetailResponse]:
    """用户端活动详情"""
    activity, prize_count = await ActivityService(db).get_public(activity_id)
    return ok(ActivityDetailResponse.model_validate(activity).model_copy(update={"prize_count": prize_count}))

@admin_router.get("", response_model=ApiResponse[PaginatedResponse[ActivityResponse]])
async def list_admin_activities(
        params: PageParams = Depends(),
        keyword: str | None = None,
        status: ActivityStatus | None = None,
        _: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[ActivityResponse]]:
    items, total = await ActivityService(db).list_admin(
        page = params.page,
        page_size = params.page_size,
        keyword = keyword,
        status = status,
    )
    return ok(
        PaginatedResponse(
            items = items,
            total = total,
            page = params.page,
            page_size = params.page_size,
        )
    )

@admin_router.post("", response_model=ApiResponse[ActivityResponse], status_code=201)
async def create_activity(
        data: ActivityCreate,
        request: Request,
        current_user: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActivityResponse]:
    """创建活动，活动的初始状态为草稿"""
    activity = await ActivityService(db).create(
        current_user, data, ip=_client_ip(request)
    )
    return ok(activity, "活动已创建")

@admin_router.get("/{activity_id}", response_model=ApiResponse[ActivityDetailResponse])
async def get_admin_activity(
        activity_id: int,
        _: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActivityDetailResponse]:
    """管理端活动详情"""
    activity, prize_count = await ActivityService(db).get_admin(activity_id)
    return ok(ActivityDetailResponse.model_validate(activity).model_copy(update={"prize_count": prize_count}))

@admin_router.put("/{activity_id}", response_model=ApiResponse[ActivityResponse])
async def update_activity(
        activity_id: int,
        data: ActivityUpdate,
        request: Request,
        current_user: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActivityResponse]:
    """更新活动"""
    activity = await ActivityService(db).update(
        current_user, activity_id, data, ip=_client_ip(request)
    )
    return ok(activity,"活动已更新")

@admin_router.delete("/{activity_id}", response_model=ApiResponse[None])
async def delete_activity(
        activity_id: int,
        request: Request,
        current_user: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) ->ApiResponse[None]:
    """删除活动"""
    await ActivityService(db).delete(current_user, activity_id, ip=_client_ip(request))
    return ok(message="活动已删除")

@admin_router.post("/{activity_id}/publish", response_model=ApiResponse[ActivityResponse])
async def publish_activity(
        activity_id: int,
        request: Request,
        current_user: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActivityResponse]:
    """发布活动： 草稿 -> 待开始（）开始时间已到则直接进行中"""
    activity = await ActivityService(db).publish(current_user, activity_id, ip=_client_ip(request))
    return ok(activity, "活动已发布")

@admin_router.post("/{activity_id}/start", response_model=ApiResponse[ActivityResponse])
async def publish_activity(
        activity_id: int,
        request: Request,
        current_user: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActivityResponse]:
    """开始活动：待开始 → 进行中。"""
    activity = await ActivityService(db).start(current_user, activity_id, ip=_client_ip(request))
    return ok(activity, "活动已开始")

@admin_router.post("/{activity_id}/pause", response_model=ApiResponse[ActivityResponse])
async def publish_activity(
        activity_id: int,
        request: Request,
        current_user: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActivityResponse]:
    """暂停活动：进行中 → 已暂停。"""
    activity = await ActivityService(db).pause(current_user, activity_id, ip=_client_ip(request))
    return ok(activity, "活动已暂停")

@admin_router.post("/{activity_id}/resume", response_model=ApiResponse[ActivityResponse])
async def publish_activity(
        activity_id: int,
        request: Request,
        current_user: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActivityResponse]:
    """恢复活动：已暂停 → 进行中。"""
    activity = await ActivityService(db).resume(current_user, activity_id, ip=_client_ip(request))
    return ok(activity, "活动已恢复")

@admin_router.post("/{activity_id}/end", response_model=ApiResponse[ActivityResponse])
async def publish_activity(
        activity_id: int,
        request: Request,
        current_user: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActivityResponse]:
    """结束活动：待开始/进行中/已暂停 → 已结束。"""
    activity = await ActivityService(db).end(current_user, activity_id, ip=_client_ip(request))
    return ok(activity, "活动已结束")