"""管理端用户服务：列表、状态、角色分配。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.exceptions import NotFoundError
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserStatusUpdate
from app.schemas.user import UserRoleUpdate


class UserService:
    """管理员操作用户的服务"""

    def __init__(self, db:AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)

    async def list_users(
            self,
            *,
            page: int = 1,
            page_size: int = 20,
            keyword: str | None = None,
            status: str | None = None,
    ) -> tuple[list[User], int]:
        return await self.users.list_users(
            page=page,
            page_size=page_size,
            keyword=keyword,
            status=status,
        )

    async def update_status(self, user_id: int, data: UserStatusUpdate) -> User:
        user = await self.users.get(user_id)
        if user is None:
            raise NotFoundError("用户不存在")
        user.status = data.status
        await self.db.flush()
        await self.db.commit()
        return user

    async def update_role(self, user_id: int, data: UserRoleUpdate) -> User:
        user = await self.users.get(user_id)
        if user is None:
            raise NotFoundError("用户不存在")
        roles = await self.roles.list_by_codes(data.role_codes)
        found = {role.code for role in roles}
        missing = set(data.role_codes) - found
        if missing:
            raise NotFoundError(f"角色不存在: {','.join(sorted(missing))}")

        user.roles = roles
        await self.db.flush()
        await self.db.commit()
        return user
