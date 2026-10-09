"""
        创建初始管理员账号
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import hash_password
from app.models.user import User, Role
from app.models.enums import RoleStatus



settings = get_settings()

DEFAULT_ROLES = [
    {"code": "admin", "name": "管理员", "sort_order": 20},
    {"code": "operator", "name": "运营人员", "sort_order": 10},
    {"code": "user", "name": "普通用户", "sort_order": 0},
]

async def main() -> None:
    #----- 先建表 -----
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        #----- 角色 -----
        for item in DEFAULT_ROLES:
            exists = (
                await db.execute(select(Role).where(Role.code == item["code"]))
            ).scalar_one_or_none()
            if exists is None:
                db.add(Role(**item, status=RoleStatus.ENABLED))
        await db.commit()
        #----- 初始化管理员 -----
        admin_role = (
            await db.execute(select(Role).where(Role.code == "admin"))
        ).scalar_one()
        admin = (
            await db.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
        ).scalar_one_or_none()
        if admin is None:
            db.add(
                User(
                    username=settings.ADMIN_USERNAME,
                    phone_number=settings.ADMIN_PHONE,
                    password_hash=hash_password(settings.ADMIN_PASSWORD),
                    roles=[admin_role],
                )
            )
            await db.commit()

    await engine.dispose()
    print("初始化已完成: 建表+角色+管理员")


if __name__ == "__main__":
    asyncio.run(main())