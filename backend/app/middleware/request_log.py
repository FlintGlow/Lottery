"""请求日志中间件： 注入request_id, 记录方法、路径、状态码与耗时"""

from __future__ import annotations

import logging
import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("app.request")

_SAFE_REQUEST_ID = re.compile(r"[^\w\-.]")


class RequestLogMiddleware(BaseHTTPMiddleware):
    """为每个请求生成request_id 并输出访问日志"""

    async def dispatch(self, request: Request, call_next):
        # 客户端传入的 X-Request-ID 只保留可打印且长度可控的字符，
        # 避免 CRLF 注入与超长关联 ID
        raw_id = request.headers.get("X-Request-ID") or ""
        request_id = _SAFE_REQUEST_ID.sub("", raw_id)[:64] or str(uuid.uuid4())
        start = time.perf_counter()
        query = f"?{request.url.query}" if request.url.query else ""
        try:
            response = await call_next(request)
        except Exception :
            logger.warning(
                "request_id = %s %s %s%s failed %.1fms client_ip=%s",
                request_id,
                request.method,
                request.url.path,
                query,
                (time.perf_counter() - start) * 1000,
                request.client.host if request.client else "-",
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_id = %s %s %s%s -> %s %.1fms client_ip=%s user=%s",
            request_id,
            request.method,
            request.url.path,
            query,
            response.status_code,
            duration_ms,
            request.client.host if request.client else "-",
            getattr(request.state, "user_id", "-"),
        )
        return response