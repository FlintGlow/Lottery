"""全局异常处理：业务异常、参数校验异常、未处理异常统一转为响应体"""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import AppError
from app.schemas.common import ApiResponse

logger = logging.getLogger(__name__)

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """业务异常 -> 对应 HTTP状态码 + 统一响应体"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(code=exc.code, message=exc.message).model_dump(),
    )


async def validation_error_handler(
        request: Request,
        exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=ApiResponse(
            code=42200,
            message="参数校验失败",
            data=jsonable_encoder(exc.errors()),
        ).model_dump(mode="json"),
    )

async def unhandled_exception_handler(
        request: Request,
        exc: Exception
) -> JSONResponse:
    logger.exception(
        "未处理异常: %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content=ApiResponse(
            code=50000,
            message="服务器内部错误"
        ).model_dump(),
    )

async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException
) -> JSONResponse:
    """把404/405等框架异常也包装成统一响应体"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(
            code=exc.status_code * 100,
            message=str(exc.detail),
            data=None,
        ).model_dump(),
        headers=getattr(exc, "headers", None),
    )

def register_exception_handlers(app) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)