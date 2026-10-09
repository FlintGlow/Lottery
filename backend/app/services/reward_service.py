"""补发业务：人工补发、状态流转、操作审计。"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.log import OperationLog
from app.models.reward import ManualReward
from app.models.enums import ManualRewardStatus, RedemptionStatus

from app.core.exceptions import NotFoundError, BadRequestError

from app.repositories.reward_repository import ManualRewardRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.lottery_repository import LotteryRepository
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.prize_repository import PrizeRepository
from app.repositories.user_repository import UserRepository

from app.schemas.reward import ManualRewardCreate, ManualRewardResponse, ManualRewardStatusUpdate
from app.core.exceptions import ConflictError
from app.models.lottery import WinRecord
from app.services.lottery_cache import LotteryCacheService
from app.services.draw_result_service import CLAIM_EXPIRE_DAYS

_ALLOWED_REWARD_TRANSITIONS:dict[ManualRewardStatus, set[ManualRewardStatus]] = {
    ManualRewardStatus.PENDING: {ManualRewardStatus.ISSUED, ManualRewardStatus.CANCELLED},
    ManualRewardStatus.ISSUED:set(),
    ManualRewardStatus.CANCELLED:set(),
}


class RewardService:
    """人工补发服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.rewards = ManualRewardRepository(db)
        self.users = UserRepository(db)
        self.prizes = PrizeRepository(db)
        self.records = LotteryRepository(db)
        self.operation_logs = OperationLogRepository(db)
        self.activities = ActivityRepository(db)
        self.cache = LotteryCacheService(self.db)

    async def create(
            self,
            operator: User,
            data: ManualRewardCreate,
    ) -> ManualRewardResponse:
        user = await self.users.get(data.user_id)
        if user is None:
            raise NotFoundError("用户不存在")
        prize = await self.prizes.get(data.prize_id)
        if prize is None:
            raise NotFoundError("奖品不存在")

        activity_id = prize.activity_id
        if data.draw_record_id is not None:
            record = await self.records.get(data.draw_record_id)
            if record is None or record.user_id != user.id:
                raise BadRequestError("抽奖记录不存在或不属于该用户")
            activity_id = record.activity_id

        reward = ManualReward(
            user_id = user.id,
            activity_id = activity_id,
            prize_id = prize.id,
            draw_record_id = data.draw_record_id,
            reason = data.reason,
            remark = data.remark,
            operator_id = operator.id,
            operator_name = operator.username,
        )
        reward = await self.rewards.add(reward)
        await self.operation_logs.add(
            OperationLog(
                user_id = operator.id,
                module = "reward",
                action = "create",
                target_type = "manual_reward",
                target_id = reward.id,
                detail_json = {
                    "user_id": user.id,
                    "prize_id": prize.id,
                    "reason": data.reason,
                },
            )
        )
        await self.db.commit()
        return await self._to_out(reward)

    async def list(
            self,
            *,
            operator: str | None = None,
            activity_id: int | None = None,
            user_id: int | None = None,
            username: str | None = None,
            phone_number: str | None = None,
            prize_id: int | None = None,
            keyword: str | None = None,
            status: str | None = None,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple[list[ManualRewardResponse], int]:
        items, total = await self.rewards.list_rewards(
            operator = operator,
            activity_id = activity_id,
            user_id = user_id,
            username = username,
            phone_number = phone_number,
            prize_id = prize_id,
            keyword = keyword,
            status = status,
            start_time = start_time,
            end_time = end_time,
            page = page,
            page_size = page_size,
        )
        return [await self._to_out(reward) for reward in items], total

    async def update_status(
            self,
            operator: User,
            reward_id: int,
            data: ManualRewardStatusUpdate,
    ) -> ManualRewardResponse:
        reward = await self.rewards.get(reward_id)
        if reward is None:
            raise NotFoundError("补发记录不存在")
        allowed = _ALLOWED_REWARD_TRANSITIONS.get(reward.status, set())
        if data.status not in allowed:
            raise BadRequestError(
                f"补发状态不能从 {reward.status.value} 变更为 {data.status.value}"
            )
        old_status = reward.status
        if (old_status == ManualRewardStatus.PENDING and data.status == ManualRewardStatus.ISSUED):
            prize = await self.prizes.get(reward.prize_id)
            if prize is None:
                raise NotFoundError("奖品不存在")
            if prize.remain_stock <= 0:
                raise BadRequestError("奖品库存不足，无法发放")
            if not await self.prizes.decrement_remain_stock(reward.prize_id):
                raise ConflictError("请稍后重试")

            # Redis 侧用原子 DECR 与数据库同向变化；
            # 不要用内存里早先读到的旧值 set_stock，否则会覆盖并发的抽奖预扣。

            if await self.cache.deduct_stock(reward.prize_id) < 0:
                # 库存键不存在或已扣到 0：按刚扣减后的数据库值重新同步
                await self.cache.set_stock(
                    reward.prize_id, max(prize.remain_stock - 1, 0)
                )

            self.db.add(
                WinRecord(
                    # 人工补发没有对应的抽奖记录，此处留空
                    draw_record_id = reward.draw_record_id,
                    user_id = reward.user_id,
                    activity_id = reward.activity_id,
                    prize_id = reward.prize_id,
                    prize_type = prize.prize_type,
                    prize_name = prize.name,
                    prize_image = prize.img_url,
                    # 与抽奖落库保持一致：补发同样生成兑换码与领取有效期
                    redemption_code = secrets.token_hex(6).upper(),
                    expire_at = datetime.now() + timedelta(days=CLAIM_EXPIRE_DAYS),
                    redemption_status = RedemptionStatus.PENDING,
                )
            )

        reward.status = data.status
        reward.operator_id = operator.id
        reward.operator_name = operator.username
        reward.operated_at = datetime.now()
        if data.remark is not None:
            reward.remark = data.remark
        await self.db.flush()
        await self.db.refresh(reward)
        await self.operation_logs.add(
            OperationLog(
                user_id = operator.id,
                module = "reward",
                action = f"update_status: {data.status.value}",
                target_type = "manual_reward",
                target_id = reward.id,
                detail_json = {"from": old_status, "to": data.status.value},
            )
        )
        await self.db.commit()
        return await self._to_out(reward)

    async def _to_out(self, reward: ManualReward) -> ManualRewardResponse:
        user = await self.users.get(reward.user_id)
        prize = await self.prizes.get(reward.prize_id)
        activity = await self.activities.get(reward.activity_id)
        return ManualRewardResponse(
            id = reward.id,
            user_id = reward.user_id,
            user_name = user.username if user else None,
            phone_number = user.phone_number if user else None,
            activity_id = reward.activity_id,
            activity_name = activity.name if activity else None,
            prize_id = reward.prize_id,
            prize_name = prize.name if prize else None,
            prize_type = prize.prize_type.value if prize else None,
            draw_record_id = reward.draw_record_id,
            reason = reward.reason,
            status = reward.status,
            operator_id = reward.operator_id,
            operator_name = reward.operator_name,
            operated_at = reward.operated_at,
            remark = reward.remark,
            created_at = reward.created_at,
        )