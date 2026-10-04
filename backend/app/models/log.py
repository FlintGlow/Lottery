"""操作日志模型"""

from __future__ import annotations

from sqlalchemy import JSON, BigInteger, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, IdMixin, TimestampMixin


class OperationLog(IdMixin, TimestampMixin, Base):
    """管理员操作日志。"""

    __tablename__ = "operation_logs"
    __table_args__ = (
        Index("ix_operation_logs_module_action", "module", "action"),
        Index("ix_operation_logs_target", "target_type", "target_id"),
    )

    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        comment="操作人ID",
    )
    module: Mapped[str] = mapped_column(String(32), nullable=False, comment="模块")
    action: Mapped[str] = mapped_column(String(64), nullable=False, comment="动作")
    target_type: Mapped[str | None] = mapped_column(String(32), comment="目标类型")
    target_id: Mapped[int | None] = mapped_column(BigInteger, comment="目标ID")
    detail_json: Mapped[dict | None] = mapped_column(JSON, comment="变更明细")
    ip: Mapped[str | None] = mapped_column(String(45), comment="操作IP")
