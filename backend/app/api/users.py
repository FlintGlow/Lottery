"""用户接口： 个人中心 + 管理端用户管理"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles,get_current_user
from app.models.user import User
from app.core.database import get_db
from app.models.enums import UserStatus
from app.schemas.common import ApiResponse, PageParams, PaginatedResponse, ok
from app.schemas.user import ChangePasswordResponse, UserResponse, UserRoleUpdate, UserStatusUpdate, UserUpdateMe
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["用户"])
admin_router = APIRouter(prefix="/admin/users", tags=["管理-用户"])


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(current_user: User = Depends(get_current_user)) -> ApiResponse[UserResponse]:
    """获取当前用户信息"""

    return ok(current_user)

@router.put("/me", response_model=ApiResponse[UserResponse])
async def update_me(
        data: UserUpdateMe,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserResponse]:
    """更新当前用户资料"""
    user = await AuthService(db).update_profile(current_user, data)
    return ok(user, "资料已更新")


@router.put("/me/password", response_model=ApiResponse[None])
async def change_my_password(
        data: ChangePasswordResponse,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    """修改当前用户密码"""
    await AuthService(db).change_password(current_user, data)
    return ok(message="密码已修改")

@admin_router.get("", response_model=ApiResponse[PaginatedResponse[UserResponse]])
async def list_users(
        parms: PageParams = Depends(),
        keyword: str | None = None,
        status: UserStatus | None = None,
        _: User = Depends(require_roles("admin")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[UserResponse]]:
    """用户分页列表"""
    items, total = await UserService(db).list_users(
        page = parms.page,
        page_size = parms.page_size,
        keyword = keyword,
        status = status.value if status else None,
    )
    return ok(
        PaginatedResponse(
            items = items,
            total = total,
            page = parms.page,
            page_size = parms.page_size,
        )
    )


@admin_router.put("/{user_id}/status", response_model=ApiResponse[UserResponse])
async def update_user_status(
        user_id: int,
        data: UserStatusUpdate,
        _: User = Depends(require_roles("admin")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserResponse]:
    """启用/禁用用户"""
    user = await UserService(db).update_status(user_id, data)
    return ok(user, "状态已更新")

@admin_router.put("/{user_id}/roles", response_model=ApiResponse[UserResponse])
async def update_user_roles(
        user_id: int,
        data: UserRoleUpdate,
        _: User = Depends(require_roles("admin")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserResponse]:
    """分配用户角色"""
    user = await UserService(db).update_role(user_id, data)
    return ok(user, "角色已更新")
