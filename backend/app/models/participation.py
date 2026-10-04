"""活动参与记录模型：手机号 + 活动 用于活动统计。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, IdMixin, TimestampMixin


class ActivityParticipation(IdMixin, TimestampMixin, Base):


    __tablename__ = "activity_participations"
    __table_args__ = (

        Index("ix_activity_participations_phone_number", "phone_number"),
    )

    activity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("activities.id", ondelete="RESTRICT"),
        nullable=False,
        comment="活动ID",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="用户ID",
    )
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, comment="参与手机号快照")
    participated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="参与时间",
    )
