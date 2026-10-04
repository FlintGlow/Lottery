"""请求日志中间件： 注入request_id, 记录方法、路径、状态码与耗时"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("app.request")


class RequestLogMiddleware(BaseHTTPMiddleware):
    """为每个请求生成request_id 并输出访问日志"""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception :
            logger.info(
                "request_id = %s %s %s failed %.1fms",
                request_id,
                request.method,
                request.url.path,
                (time.perf_counter() - start) * 1000,
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_id = %s %s %s -> %s %.1fms client_ip= %s user=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request.client.host if request.client else "-",
            getattr(request.state, "user_id", "-"),
        )
        return response