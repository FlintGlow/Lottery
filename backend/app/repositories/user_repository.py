"""用户 仓储。"""

from __future__ import annotations

from sqlalchemy import select, func, or_

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_username(self, username: str) -> User | None:
        return await self.get_by(username=username)

    async def get_by_phone(self, phone_number: str) -> User | None:
        return await self.get_by(phone_number=phone_number)

    async def list_users(
            self,
            *,
            page: int = 1,
            page_size: int = 20,
            keyword: str | None = None,
            status: str | None = None,
    ) -> tuple[list[User], int]:
        """用户分页列表，支持关键字（用户名/昵称/邮箱/手机号）与状态筛选。"""
        conditions = [User.is_deleted.is_(False)]
        if status:
            conditions.append(User.status == status)
        if keyword:
            like = f'%{keyword}%'
            conditions.append(
                or_(
                    User.username.like(like),
                    User.phone_number.like(like),
                )
            )
        total = (
            await self.session.execute(
                select(func.count()).select_from(User).where(*conditions)
            )
        ).scalar_one()
        stmt = (
            select(User)
            .where(*conditions)
            .order_by(User.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total