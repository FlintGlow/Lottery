from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, String, func, JSON, BigInteger, Index,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column, relationship

from app.core.database import Base, IdMixin, TimestampMixin, SoftDeleteMixin

from app.models.enums import DrawStatus, RedemptionStatus, PrizeType, enum_column


class DrawRecord(IdMixin, TimestampMixin, SoftDeleteMixin,Base):
    __tablename__ = "draw_records"
    __table_args__ = (
        Index("ix_draw_records_user_activity_time", "user_id", "activity_id", "created_at"),
        Index("ix_draw_records_activity_status", "activity_id", "status")
    )

    order_no: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True, comment="抽奖流水号")
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id",ondelete="RESTRICT"),
        index=True,
        nullable=False,
        comment="用户ID",
    )
    activity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("activities.id",ondelete="RESTRICT"),
        index=True,
        nullable=False,
        comment="活动ID"
    )
    prize_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("prizes.id",ondelete="RESTRICT"),
        index=True,
        comment="中奖的奖品ID"
    )
    status: Mapped[DrawStatus] = mapped_column(
        enum_column(DrawStatus, "draw_status"),
        default=DrawStatus.PENDING,
        nullable=False,
        comment="记录状态",
    )
    result_json: Mapped[dict | None] = mapped_column(JSON, comment="结果快照")
    ip: Mapped[str | None] = mapped_column(String(45), comment="客户端IP")
    error_message: Mapped[str | None] = mapped_column(String(255), comment="失败原因")

    win_record: Mapped[WinRecord | None] = relationship(
        back_populates="draw_record",
        uselist=False,
    )


class WinRecord(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "win_records"
    __table_args__ = (
        UniqueConstraint("draw_record_id", name="uk_win_records_lottery_record"),
        Index("ix_win_records_user_redemption", "user_id", "redemption_status"),
        Index("ix_win_records_activity_prize", "activity_id", "prize_id"),
    )

    draw_record_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("draw_records.id",ondelete="RESTRICT"),
        nullable=True,
        comment="抽奖记录ID；人工补发生成的中奖记录没有对应抽奖记录，此处为空",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id",ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="用户ID",
    )
    activity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("activities.id",ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="活动ID",
    )
    prize_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("prizes.id",ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="奖品ID",
    )
    prize_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="奖品名称")
    prize_image: Mapped[str | None] = mapped_column(String(255), comment="奖品图片")
    redemption_status: Mapped[RedemptionStatus] = mapped_column(
        enum_column(RedemptionStatus, "redemption_status"),
        default=RedemptionStatus.PENDING,
        nullable=False,
        comment="领取状态",
    )
    prize_type: Mapped[PrizeType] = mapped_column(
        enum_column(PrizeType, "prize_type"),
        default=PrizeType.PHYSICAL,
        nullable=False,
        comment="奖品类型"
    )
    redemption_code: Mapped[str | None] = mapped_column(String(32), unique=True, comment="兑换码")
    recipient_name: Mapped[str | None] = mapped_column(String(64),comment="收货人姓名")
    recipient_phone: Mapped[str | None] = mapped_column(String(20), comment="收货电话")
    recipient_address: Mapped[str | None] = mapped_column(String(255), comment="收货地址")
    redemption_at: Mapped[datetime | None] = mapped_column(DateTime, comment="领取时间")
    expire_at: Mapped[datetime | None] = mapped_column(DateTime, comment="领取过期时间")
    processed_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id",ondelete="RESTRICT"),
        comment="处理人（运营/管理员）"
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, comment="处理时间")
    process_remark: Mapped[str | None] = mapped_column(String(255), comment="处理备注")

    draw_record: Mapped[DrawRecord] = relationship(back_populates="win_record")

