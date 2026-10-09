"""用户 Schema"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict

from datetime import datetime
from app.models.enums import UserStatus
from app.schemas.role import RoleResponse


class UserUpdateMe(BaseModel):
    name: str | None = Field(
        max_length=64,
        min_length=1,
        default=None,
        pattern=r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$',
        description="用户名",
    )
    phone_number: str | None = Field(max_length=20, pattern=r'^1[3-9]\d{9}$', default=None)
    avatar_url: str | None = Field(default=None, max_length=255)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:int
    username: str
    phone_number: str | None
    avatar_url: str | None
    status: UserStatus
    last_login: datetime | None = Field(validation_alias="last_login_at")
    created_at: datetime
    roles: list[RoleResponse] = []


class ChangePasswordResponse(BaseModel):
    old_password: str = Field(min_length=1, max_length=64)
    new_password: str = Field(min_length=8, max_length=64)


class UserStatusUpdate(BaseModel):
    status: UserStatus


class UserRoleUpdate(BaseModel):
    role_codes: list[str] = Field(min_length=1, max_length=64, description="角色编码列表")