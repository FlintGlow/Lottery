from __future__ import annotations

from sqlalchemy import  ForeignKey, Integer, String, CheckConstraint, BigInteger, Index, Text
from sqlalchemy.orm import Mapped,mapped_column, relationship

from app.core.database import Base, IdMixin, SoftDeleteMixin, TimestampMixin

from app.models.enums import PrizeType, PrizeStatus,enum_column


class PrizeCategory(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    """奖品分类。"""

    __tablename__ = "prize_categories"

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="分类名称")
    description: Mapped[str | None] = mapped_column(String(255), comment="分类描述")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="排序")
    status: Mapped[PrizeStatus] = mapped_column(
        enum_column(PrizeStatus, "prize_status"),
        default=PrizeStatus.ENABLED,
        nullable=False,
        index=True,
        comment="状态",
    )

    prizes: Mapped[list[Prize]] = relationship(back_populates="category")


class Prize(IdMixin, TimestampMixin, SoftDeleteMixin, Base):

    __tablename__ = "prizes"
    __table_args__ = (
        Index("ix_prizes_activity_status", "activity_id", "status"),
        Index("ix_prizes_category_id", "category_id"),
        CheckConstraint("total_stock >= 0", name="ck_prizes_total_stock"),
        CheckConstraint("remain_stock >= 0", name="ck_prizes_remain_stock"),
        CheckConstraint("weight >= 0", name="ck_prizes_weight"),
    )

    activity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("activities.id", ondelete="RESTRICT"),
        nullable=False,
        comment="活动ID"
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("prize_categories.id", ondelete="RESTRICT"),
        comment="分类ID"
    )
    prize_type: Mapped[PrizeType] = mapped_column(
        enum_column(PrizeType, "prize_type"),
        default=PrizeType.PHYSICAL,
        nullable=False,
        comment="奖品类型",
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="奖品名称")
    prize_level: Mapped[str | None] = mapped_column(String(32), comment="奖品等级")
    description: Mapped[str | None] = mapped_column(Text, comment="奖品描述")
    total_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="总库存量")
    remain_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="剩余库存量")
    weight: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="中奖权重(0=不参与)")
    img_url: Mapped[str | None] = mapped_column(String(255), comment="奖品图片")
    status: Mapped[PrizeStatus] = mapped_column(
        enum_column(PrizeStatus, "prize_status"),
        default=PrizeStatus.ENABLED,
        nullable=False,
        comment="状态"
    )
    sort_order: Mapped[int] = mapped_column(Integer,default=0, nullable=False, comment="排序")
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="乐观锁版本号")

    activity: Mapped[Activity] = relationship(back_populates="prizes")
    category: Mapped[PrizeCategory | None] = relationship(back_populates="prizes")
