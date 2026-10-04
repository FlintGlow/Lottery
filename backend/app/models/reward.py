from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, IdMixin, SoftDeleteMixin, TimestampMixin
from app.models.enums import ManualRewardStatus, enum_column


class ManualReward(IdMixin, TimestampMixin, SoftDeleteMixin, Base):


    __tablename__ = "manual_rewards"
    __table_args__ = (
        Index("ix_manual_rewards_status", "status"),
        Index("ix_manual_rewards_user_id", "user_id"),
        Index("ix_manual_rewards_activity_id", "activity_id"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="补发用户ID",
    )
    activity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("activities.id", ondelete="RESTRICT"),
        nullable=False,
        comment="活动ID",
    )
    prize_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("prizes.id", ondelete="RESTRICT"),
        nullable=False,
        comment="补发奖品ID",
    )
    draw_record_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("draw_records.id", ondelete="RESTRICT"),
        comment="关联抽奖记录ID(选填)",
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False, comment="补发原因")
    status: Mapped[ManualRewardStatus] = mapped_column(
        enum_column(ManualRewardStatus, "manual_reward_status"),
        default=ManualRewardStatus.PENDING,
        nullable=False,
        comment="补发状态",
    )
    operator_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        comment="操作人员ID",
    )
    operator_name: Mapped[str | None] = mapped_column(
        String(64),
        comment="操作人员名称快照（改用户名不影响历史记录）",
    )
    operated_at: Mapped[datetime | None] = mapped_column(DateTime, comment="操作时间")
    remark: Mapped[str | None] = mapped_column(String(255), comment="备注")
