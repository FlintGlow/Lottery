"""角色管理服务"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.role_repository import RoleRepository
from app.models.user import Role
from app.schemas.role import RoleCreate, RoleUpdate
from app.core.exceptions import ConflictError, NotFoundError


class RoleService:
    """角色 CRUD 与使用约束校验"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.roles = RoleRepository(db)

    async def list_roles(self) -> list[Role]:
        roles, _ = await self.roles.list(
            page = 1,
            page_size = 100,
            order_by = Role.sort_order,
            descending = False,
        )
        return roles

    async def create_role(self, data: RoleCreate) -> Role:
        if await self.roles.get_by_code(data.code):
            raise ConflictError("角色编码已存在")
        role = Role(
            code = data.code,
            name = data.name,
            description = data.description,
            sort_order = data.sort_order,
        )
        role = await self.roles.add(role)
        await self.db.commit()
        return role

    async def update_role(self, role_id: int,data: RoleUpdate) -> Role:
        role = await self.roles.get(role_id)
        if role is None:
            raise NotFoundError("角色不存在")
        if data.name is not None:
            role.name = data.name
        if data.description is not None:
            role.description = data.description
        if data.status is not None:
            role.status = data.status
        if data.sort_order is not None:
            role.sort_order = data.sort_order
        await self.db.flush()
        await self.db.commit()
        return role

    async def delete_role(self, role_id: int) -> None:
        role = await self.roles.get(role_id)
        if role is None:
            raise NotFoundError("角色不存在")
        assigned = await self.roles.count_user_roles(role_id)
        if assigned > 0:
            raise ConflictError("角色仍被用户使用，无法删除")
        role.is_deleted = True
        await self.db.flush()
        await self.db.commit()