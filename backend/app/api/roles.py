"""角色管理接口（仅 admin）"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.user import User
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from app.schemas.common import ApiResponse, ok
from app.services.role_service import RoleService

router = APIRouter(prefix="/admin/roles", tags=["管理-角色"])

@router.get("", response_model=ApiResponse[list[RoleResponse]])
async def list_roles(
        _: User = Depends(require_roles("admin")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[RoleResponse]]:
    """用户列表"""
    return ok(await RoleService(db).list_roles())


@router.post("", response_model=ApiResponse[RoleResponse], status_code=201)
async def create_role(
        data: RoleCreate,
        _: User = Depends(require_roles("admin")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[RoleResponse]:
    """创建角色"""
    return ok(await RoleService(db).create_role(data), "角色已创建")


@router.put("/{role_id}", response_model=ApiResponse[RoleResponse])
async def update_role(
        role_id: int,
        data: RoleUpdate,
        _: User = Depends(require_roles("admin")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[RoleResponse]:
    """更新角色"""
    return ok(await RoleService(db).update_role(role_id, data), "角色已更新")


@router.delete("/{role_id}", response_model=ApiResponse[None])
async def delete_role(
        role_id: int,
        _: User = Depends(require_roles("admin")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    """删除角色（软删除， 被引用时拒绝）"""
    await RoleService(db).delete_role(role_id)
    return ok(message="角色已删除")