

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Index, DateTime, ForeignKey, Integer,String, UniqueConstraint, BigInteger
from sqlalchemy.orm import Mapped,mapped_column, relationship

from app.core.database import Base,IdMixin, TimestampMixin, SoftDeleteMixin
from app.models.enums import UserStatus, enum_column, RoleStatus


class User(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False,comment="用户名")
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, comment="手机号")
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False, comment="密码哈希(BCrypt)")
    avatar_url: Mapped[str | None] = mapped_column(String(255), comment="头像地址")
    roles : Mapped[list[Role]] = relationship(
        secondary="user_roles",
        back_populates="users",
        lazy="selectin"
    )
    status: Mapped[UserStatus] = mapped_column(
        enum_column(UserStatus, "user_status"),
        default=UserStatus.ACTIVE,
        nullable=False,
        index=True,
        comment="账号状态"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime,comment="最后登录时间")


class Role(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "roles"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, comment="角色编码")
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="角色名称")
    description: Mapped[str | None] = mapped_column(String(255),comment="角色描述")
    status: Mapped[RoleStatus] = mapped_column(
        enum_column(RoleStatus, "role_status"),
        default=RoleStatus.ENABLED,
        nullable=False,
        index=True,
        comment="角色状态",
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="排序")

    users: Mapped[list[User]] = relationship(
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin"
    )


class UserRole(IdMixin, TimestampMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uk_user_role"),
        Index("ix_user_roles_role_id", "role_id"),
    )

    user_id: Mapped[str] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="用户ID"
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        comment="角色ID",
    )