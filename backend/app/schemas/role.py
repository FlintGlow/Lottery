"""角色 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RoleStatus


class RoleCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32, pattern=r"^[a-z][a-z0-9_]*$", description="角色编码")
    name: str = Field(min_length=1, max_length=64, description="角色名称")
    description: str | None = Field(description=None, max_length=255)
    sort_order: int = Field(default=0, ge=0)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    status: RoleStatus | None = Field(default=None)
    sort_order: int | None = Field(default=None, ge=0)


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None
    sort_order: int
    status: RoleStatus