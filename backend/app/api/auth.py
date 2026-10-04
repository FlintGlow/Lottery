"""认证接口： 登录、注册、刷新、登出"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.schemas.auth import LoginRequest, LogoutRequest, RegisterRequest, RefreshRequest, TokenPair
from app.schemas.common import ApiResponse, ok
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["认证"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None

@router.post("/register", response_model=ApiResponse[TokenPair], status_code= 201)
async def register(
        data: RegisterRequest,
        request: Request,
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenPair]:
    """注册并自动登录"""
    tokens = await AuthService(db).register(data, ip=_client_ip(request))
    return ok(tokens, "注册成功")


@router.post("/login", response_model=ApiResponse[TokenPair])
async def login(
        data: LoginRequest,
        request: Request,
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenPair]:
    tokens = await AuthService(db).login(data, ip=_client_ip(request))
    return ok(tokens, "登录成功")

@router.post("/refresh", response_model=ApiResponse[TokenPair])
async def refresh(
        data: RefreshRequest,
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenPair]:
    """刷新 Access Token"""
    return ok(await AuthService(db).refresh(data))

@router.post("/logout", response_model=ApiResponse[None])
async def logout(
        data: LogoutRequest,
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    await AuthService(db).logout(data)
    return ok(message="已登出")