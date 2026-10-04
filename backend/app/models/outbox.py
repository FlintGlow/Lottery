"""MQ 出站消息表（事务性发件箱）：保证"预扣成功但消息丢失"不发生。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, IdMixin, TimestampMixin
from app.models.enums import OutboxStatus, enum_column


class MessageOutbox(IdMixin, TimestampMixin, Base):
    """待发送消息。"""

    __tablename__ = "message_outbox"
    __table_args__ = (
        Index("ix_message_outbox_status_next_retry", "status", "next_retry_at"),
    )

    biz_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="业务类型")
    biz_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="业务号")
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, comment="消息体")
    exchange: Mapped[str] = mapped_column(String(64), nullable=False, comment="交换机")
    routing_key: Mapped[str] = mapped_column(String(64), nullable=False, comment="路由键")
    status: Mapped[OutboxStatus] = mapped_column(
        enum_column(OutboxStatus, "outbox_status"),
        default=OutboxStatus.PENDING,
        nullable=False,
        index=True,
        comment="发送状态",
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="重试次数")
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, comment="下次重试时间")
    last_error: Mapped[str | None] = mapped_column(String(255), comment="最近错误")
