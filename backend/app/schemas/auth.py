"""认证相关的Schema"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=64,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="用户名",
    )
    password: str = Field(
        min_length=8,
        max_length=64,
        description="密码",
    )
    phone_number: str = Field(pattern=r'^1[3-9]\d{9}$',description="手机号(必填)")


class LoginRequest(BaseModel):
    account: str = Field(min_length=1, max_length=128, description="手机号/用户名")
    password: str = Field(min_length=8, max_length=64, description="密码")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, description="刷新令牌")


class LogoutRequest(BaseModel):
    token: str = Field(min_length=1, description="要注销的令牌")


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
    expires_in: int = Field(description="Access Token 有效期(秒)")