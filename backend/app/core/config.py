from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 示例密钥：非开发环境必须通过环境变量覆盖
_INSECURE_JWT_DEFAULT = "change-me-in-production-with-random-32-plus-bytes"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    # ---- 应用 ----
    APP_NAME: str = "lottery"
    APP_ENV: str = "dev"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # ---- MySQL ----
    DATABASE_URL: str = "mysql+asyncmy://root:123456@localhost:3306/lottery?charset=utf8mb4"

    # ---- Redis ----
    REDIS_URL: str = "redis://localhost:6379/0"

    # ---- RabbitMQ ----
    RABBITMQ_URL: str = "amqp://lottery:lottery123456@localhost:5672/lottery"

    # ---- RabbitMQ 队列----
    DRAW_QUEUE: str = "lottery.draw"
    DRAW_EXCHANGE: str = "lottery.topic"
    DRAW_DLX: str = "lottery.dlx"
    DRAW_DLQ: str = "lottery.draw.dead"

    # ---- MinIO ----
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "lottery"
    MINIO_SECRET_KEY: str = "lottery123"
    MINIO_BUCKET: str = "lottery"
    MINIO_PUBLIC_URL: str = "http://localhost:9000"
    MINIO_SECURE: bool = False
    MINIO_UPLOAD_MAX_SIZE: int = 5 * 1024 * 1024

    # ---- JWT ----
    JWT_SECRET_KEY: str = _INSECURE_JWT_DEFAULT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---- 雪花 ID ----
    SNOWFLAKE_WORKER_ID: int = 1
    SNOWFLAKE_DATACETER_ID: int = 0

    # ---- 初始管理员（scripts/seed_admin.py 使用）----
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123456"
    ADMIN_PHONE: str = "13900000000"

    @model_validator(mode="after")
    def _reject_insecure_defaults(self):
        """非开发环境禁止使用示例密钥，避免带着公开可知的密钥上线。"""
        if self.APP_ENV == "dev":
            return self
        if (self.JWT_SECRET_KEY == _INSECURE_JWT_DEFAULT
                or len(self.JWT_SECRET_KEY) < 32):
            raise ValueError(
                "非开发环境必须通过环境变量 JWT_SECRET_KEY "
                "提供至少 32 字符的随机密钥"
            )
        return self



@lru_cache
def get_settings()-> Settings:
    return Settings()