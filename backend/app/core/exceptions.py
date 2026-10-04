"""统一业务异常体系。

Service 层抛出业务异常，全局异常处理器将其转换为统一响应体。
code 约定：HTTP 状态码 + 两位序号，如 40101。
"""


class AppError(Exception):
    """业务异常基类。"""

    def __init__(self, message: str, code: int = 40000, status_code: int = 400) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code


class BadRequestError(AppError):
    def __init__(self, message: str = "请求参数错误", code: int = 40000) -> None:
        super().__init__(message, code = code, status_code=400)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "未认证或令牌无效", code: int = 40100) -> None:
        super().__init__(message, code=code, status_code=401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "没有操作权限", code: int = 40300) -> None:
        super().__init__(message, code=code, status_code=403)


class NotFoundError(AppError):
    def __init__(self, message: str = "资源不存在", code: int = 40400) -> None:
        super().__init__(message, code=code, status_code=404)


class ConflictError(AppError):
    def __init__(self, message: str = "资源冲突", code: int = 40900) -> None:
        super().__init__(message, code=code, status_code=409)


class TooManyRequestsError(AppError):
    def __init__(self, message: str = "请求过于频繁，请稍后再试", code: int = 42900) -> None:
        super().__init__(message, code=code, status_code=429)


class TokenError(AppError):
    """令牌解析失败（签名无效或已过期）。"""

    def __init__(self, message: str = "无效或过期的令牌", code: int = 40101) -> None:
        super().__init__(message, code=code, status_code=401)
