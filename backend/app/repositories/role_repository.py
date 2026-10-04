"""角色 仓储。"""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.user import Role, UserRole
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    model = Role

    async def get_by_code(self, code: str) -> Role | None:
        return await self.get_by(code=code)

    async def list_by_codes(self, codes: list[str]) -> list[Role]:
        if not codes:
            return []
        stmt = select(Role).where(Role.code.in_(codes), Role.is_deleted.is_(False))
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows)

    async def count_user_roles(self, role_id: int) -> int:
        """统计角色当前被多少用户引用"""
        stmt = select(func.count()).select_from(UserRole).where(UserRole.role_id == role_id)
        return (await self.session.execute(stmt)).scalar_one()