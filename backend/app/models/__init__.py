from app.core.database import Base

from .user import User, Role, UserRole
from .activity import Activity
from .prize import Prize, PrizeCategory
from .lottery import DrawRecord, WinRecord
from .log import OperationLog
from .outbox import MessageOutbox
from .participation import ActivityParticipation
from .reward import ManualReward
from .enums import (
    ActivityStatus,
    PrizeType,
    PrizeStatus,
    DrawStatus,
    RedemptionStatus,
    UserStatus,
    RoleStatus,
    ManualRewardStatus,
    OutboxStatus,
)

__all__=[
    "Base",
    "User",
    "Role",
    "UserRole",
    "Activity",
    "Prize",
    "PrizeCategory",
    "DrawRecord",
    "WinRecord",
    "OperationLog",
    "MessageOutbox",
    "ActivityParticipation",
    "ManualReward",
    "UserStatus",
    "RoleStatus",
    "ActivityStatus",
    "PrizeStatus",
    "DrawStatus",
    "RedemptionStatus",
    "OutboxStatus",
]