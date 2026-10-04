"""全局枚举定义：状态字段统一使用字符串值，数据库存储可读值。"""

from enum import Enum

from sqlalchemy import Enum as SqlEnum

class UserStatus(str, Enum):
    ACTIVE = "active"       #正常
    DISABLED = "disabled"   #禁用


class RoleStatus(str, Enum):
    ENABLED = "enabled"      # 启用
    DISABLED = "disabled"    # 禁用


class ActivityStatus(str, Enum):
    DRAFT = "draft"         #草稿
    PENDING = "pending"     # 待开始
    ONGOING = "ongoing"     # 进行中
    PAUSED = "paused"       # 已暂停
    ENDED = "ended"         # 已结束


class PrizeType(str, Enum):
    PHYSICAL = "physical"       #实物
    VIRTUAL = "virtual"         #虚拟

class PrizeStatus(str, Enum):
    ENABLED = "enabled"      # 启用
    DISABLED = "disabled"    # 禁用


class DrawStatus(str, Enum):
    PENDING = "pending"     # 已预扣库存，等待异步落库
    WON = "won"             # 中奖
    NO_PRIZE = "no_prize"   # 未中奖
    FAILED = "failed"       # 处理失败（进入对账补偿）
    REFUNDED = "refunded"   # 库存已回补


class RedemptionStatus(str, Enum):
    PENDING = "pending"  # 待填写领奖信息
    SUBMITTED = "submitted"  # 已提交领奖信息
    PROCESSING = "processing"  # 运营处理中
    COMPLETED = "completed"  # 已发放
    CANCELLED = "cancelled"  # 已取消


class ManualRewardStatus(str, Enum):
    PENDING = "pending"          # 待发放
    ISSUED = "issued"            # 已发放
    CANCELLED = "cancelled"      # 已取消


class OutboxStatus(str, Enum):
    PENDING = "pending"      # 待发送
    SENT = "sent"            # 已发送
    FAILED = "failed"        # 发送失败


def enum_column(enum_cls: type[Enum], name: str) -> SqlEnum:
    """构造存储值为字符串（而非枚举名）的 SQLAlchemy Enum 类型。"""
    return SqlEnum(
        enum_cls,
        name=name,
        values_callable=lambda values: [item.value for item in values],
    )
