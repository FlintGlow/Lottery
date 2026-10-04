"""抽奖活动模型。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, BigInteger, Text, String, JSON, Index, Integer
from sqlalchemy.orm import Mapped,mapped_column, relationship

from app.core.database import Base, TimestampMixin, IdMixin, SoftDeleteMixin

from app.models.enums import ActivityStatus, enum_column


class Activity(IdMixin, TimestampMixin, SoftDeleteMixin,Base):

    __tablename__ = "activities"
    __table_args__ = (
        Index("ix_activities_status_period", "status", "start_time", "end_time"),
        Index("ix_activities_created_by", "created_by"),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="活动名称")
    description: Mapped[str | None] = mapped_column(Text, comment="活动描述")
    cover_url: Mapped[str | None] = mapped_column(String(255), comment="封面图")
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[ActivityStatus] = mapped_column(
        enum_column(ActivityStatus, "activity_status"),
        default=ActivityStatus.DRAFT,
        nullable=False,
        comment="活动状态"
    )
    daily_draw_limit: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="每人每日抽奖次数（0 = 不限）",
    )
    total_draw_limit: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="活动总抽奖次数上限（0=不限）",
    )
    rule_config: Mapped[dict | None] = mapped_column(JSON, comment="扩展规则配置")
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        comment="创建人ID",
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime, comment="发布时间")

    prizes: Mapped[list[Prize]] = relationship(back_populates="activity")

