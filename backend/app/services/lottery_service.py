"""抽奖核心业务：状态校验、每日限次、防重锁、权重算法、Redis 预扣、MQ 投递。"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone

from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import BadRequestError, NotFoundError, ConflictError, TooManyRequestsError
from app.core.rabbitmq import publish_message
from app.core.redis import get_redis
from app.models.enums import ActivityStatus, OutboxStatus
from app.models.outbox import MessageOutbox
from app.models.participation import ActivityParticipation
from app.models.user import User
from app.repositories.lottery_repository import LotteryRepository
from app.repositories.message_outbox_repository import MessageOutboxRepository
from app.repositories.participation_repository import ParticipationRepository
from app.schemas.lottery import DrawResultOut, LotteryRecordResponse
from app.services.activity_service import ActivityService
from app.services.lottery_cache import LotteryCacheService
from app.utils.snowflake import next_id

settings = get_settings()

DEFAULT_NONE_WEIGHT = 1000   # 未中奖区间权重（可被活动 rule_config.none_weight 覆盖）
DRAW_LOCK_TTL = 5            # 防重锁 TTL（秒）
DAILY_KEY_TTL = 86400        # 每日限次计数 TTL（秒）
PARTICIPATE_LOCK_TTL = 5     #参与资格锁TTL（秒）


class LotteryService:
    """抽奖服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.activities = ActivityService(db)
        self.cache = LotteryCacheService(db)
        self.records = LotteryRepository(db)
        self.outbox = MessageOutboxRepository(db)
        self.participation = ParticipationRepository(db)

    async def draw(self, user: User, activity_id: int, ip: str | None = None) -> DrawResultOut:
        """执行一次抽奖：预扣库存 → 投递消息 → 返回处理中。"""

        activity, _ = await self.activities.get_admin(activity_id)
        if activity.status != ActivityStatus.ONGOING:
            raise BadRequestError(f"活动当前不可抽奖（状态：{activity.status.value}）")

        redis = await get_redis()
        phone = user.phone_number

        lock_key = f"lottery:draw:lock:{activity_id}:{user.id}"
        lock_token = str(uuid.uuid4())
        if not await redis.set(lock_key, lock_token, nx=True, ex=DRAW_LOCK_TTL):
            raise TooManyRequestsError("抽奖处理中，请勿重复操作")
        try:
            await self._check_limit(redis, activity, user)
            candidates = await self.cache.load_candidates(activity_id)
            prize_id = await self._pick_and_deduct(
                candidates, self._none_weight(activity)
            )

            order_no = str(next_id())
            payload = {
                "order_no": order_no,
                "user_id": user.id,
                "activity_id": activity_id,
                "prize_id": prize_id,
                "ip": ip,
                "draw_at": datetime.now(timezone.utc).isoformat(),
            }
            participation = ActivityParticipation(
                activity_id=activity_id,
                user_id=user.id,
                phone_number=phone,
            )
            await self._commit_draw(payload, participation)

            return DrawResultOut(order_no=order_no)
        finally:
            await self.cache.release_lock(lock_key, lock_token)


    async def list_my_records(
            self,
            user:User,
            *,
            activity_id: int |None = None,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple[list[LotteryRecordResponse], int]:
        items, total = await self.records.list_by_user(
            user_id=user.id,
            activity_id=activity_id,
            page=page,
            page_size=page_size,
        )
        win_map = await self.records.win_id_map([record.id for record in items])
        outs = [
            LotteryRecordResponse(
                order_no = record.order_no,
                activity_id = record.activity_id,
                prize_id = record.prize_id,
                status = record.status,
                result_json=record.result_json,
                error_message=record.error_message,
                created_at=record.created_at,
                win_id=win_map.get(record.id),
            )
            for record in items
        ]
        return outs, total

    async def get_my_record(self, uer: User, order_no: str) -> LotteryRecordResponse:
        record = await self.records.get_by_order_no(order_no)
        if record is None or record.user_id != uer.id:
            raise NotFoundError("抽奖记录不存在")
        win_map = await self.records.win_id_map([record.id])
        return LotteryRecordResponse(
            order_no = record.order_no,
            activity_id = record.activity_id,
            prize_id = record.prize_id,
            status = record.status,
            result_json = record.result_json,
            error_message = record.error_message,
            created_at = record.created_at,
            win_id = win_map.get(record.id),
        )

    # ---- 内部方法 ----

    async def _check_limit(self, redis, activity, user: User) -> None:
        today = datetime.now().strftime("%Y%m%d")

        #先检查活动总抽奖次数上限
        if activity.total_draw_limit > 0:
            key = f"lottery:total:{activity.id}"
            if await redis.incr(key) > activity.total_draw_limit:
                await redis.decr(key)
                raise TooManyRequestsError(f"活动抽奖总次数已达上限({activity.total_draw_limit}次)")

        #检查当日抽奖次数（如果活动设置的每天抽奖次数 <= 0 时 直接返回， 否则设置锁记录抽奖次数和过期时间，当抽奖次数大于设置的每日抽奖次数返回已达上限）

        limit = activity.daily_draw_limit
        if limit <= 0:
            return
        key = f"lottery:user:today:{activity.id}:{user.id}:{today}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, DAILY_KEY_TTL)
        if count > limit:
            raise TooManyRequestsError(f"今日抽奖已达上限（{limit}次）")


    def _none_weight(self, activity) -> int:
        config = activity.rule_config or {}
        try:
            return max(0, int(config.get("none_weight", DEFAULT_NONE_WEIGHT)))
        except (TypeError, ValueError):
            return DEFAULT_NONE_WEIGHT

    async def _pick_and_deduct(self, candidates: list, none_weight: int) -> int | None:
        """权重累计区间随机， 若命中奖品后原子预扣，无货返回未中奖"""
        total_weight = sum(c.weight for c in candidates)
        upper = total_weight + none_weight
        if upper <= 0:
            return None
        roll = random.randint(1, upper)
        #  随机区间大于所有奖品权重总和时，为未中奖
        if roll > total_weight:
            return None

        cumulative = 0
        for candidate in candidates:
            cumulative += candidate.weight
            if roll <= cumulative:
                stock = await self.cache.deduct_stock(candidate.prize_id)
                return candidate.prize_id if stock >= 0 else None
        return None


    async def _commit_draw(
            self,
            payload: dict,
            participation: ActivityParticipation,
    ) -> None:
        """参与记录 + 发件箱在同一事务提交；唯一约束冲突视为重复参与。"""
        outbox = MessageOutbox(
            biz_type = "draw_result",
            biz_id = payload["order_no"],
            payload = jsonable_encoder(payload),
            exchange = settings.DRAW_EXCHANGE,
            routing_key = settings.DRAW_QUEUE,
            status = OutboxStatus.PENDING,
        )
        self.db.add(participation)
        await self.outbox.add(outbox)

        await self.db.commit()

        try:
            await publish_message(settings.DRAW_EXCHANGE, settings.DRAW_QUEUE, payload)
            outbox.status = OutboxStatus.SENT
            await self.db.flush()
            await self.db.commit()
        except Exception as exc:
            #消息保持 PENDING ,由补偿任务重发
            outbox.last_error = str(exc)[:255]
            await self.db.flush()
            await self.db.commit()