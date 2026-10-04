"""通用Schema: 统一响应体、分页参数与分页结果。"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应体：code=0 表示成功"""


    code: int = 0
    message: str = "success"
    data: T | None = None


class PageParams(BaseModel):
    """分页查询参数（作为依赖注入）"""


    page: int = Field(default=1 ,ge=1, description="页码")
    page_size: int = Field(default=20 ,ge=1, le=100, description="每页参数")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页结果"""

    items: list[T]
    total: int
    page: int
    page_size: int


def ok(data: T | None = None, message: str ="success") -> ApiResponse[T]:
    """构造成功响应"""
    return ApiResponse(code=0, message=message, data=data)



