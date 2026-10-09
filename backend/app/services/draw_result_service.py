"""抽奖结果落库服务：消费端最终一致性（幂等写入 + MySQL 库存扣减）。"""

from __future__ import annotations

import secrets

from datetime import datetime, timedelta
from fastapi.encoders import jsonable_encoder
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.lottery_repository import LotteryRepository
from app.services.lottery_cache import LotteryCacheService
from app.models.lottery import DrawRecord, WinRecord
from app.models.enums import DrawStatus
from app.repositories.prize_repository import PrizeRepository

CLAIM_EXPIRE_DAYS = 30


class DrawResultService:
    """消费端落库：抽奖记录 + 中奖记录 + MySQL 库存扣减。"""

    def __init__(self, db:AsyncSession):
        self.db = db
        self.records =LotteryRepository(db)
        self.prizes = PrizeRepository(db)
        self.cache = LotteryCacheService(db)

    async def persist(self, payload: dict) -> bool:
        """幂等落库，返回是否首次处理（重复消息返回 False 供直接确认）。"""
        order_no = payload["order_no"]
        if await self.records.get_by_order_no(order_no):
            return False

        record =  DrawRecord(
            order_no=order_no,
            user_id=payload["user_id"],
            activity_id=payload["activity_id"],
            prize_id=payload.get("prize_id"),
            status=DrawStatus.PENDING,
            result_json=jsonable_encoder(payload),
            ip=payload.get("ip"),
        )
        self.db.add(record)
        try:
            await self.db.flush()
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            return False    # 并发重复：唯一约束兜底

        prize_id = payload.get("prize_id")
        if prize_id is None:
            return await self._settle(record, DrawStatus.NO_PRIZE)

        prize = await self.prizes.get(prize_id)
        if prize is None:
            # 先抢占结算，抢到才回补，避免与补偿任务重复回补
            return await self._settle_with_refund(
                record, DrawStatus.REFUNDED, "奖品不存在，已回补Redis预扣", prize_id
            )

        # 数据库侧原子扣减：仅当 remain_stock > 0 才会成功
        if not await self.prizes.decrement_remain_stock(prize_id):
            # Redis 预扣与 MySQL 库存不一致：回补预扣并标记 REFUNDED
            return await self._settle_with_refund(
                record, DrawStatus.REFUNDED, "MySQL库存不足，已回补Redis预扣", prize_id
            )

        # 奖品维度的每日中出上限（prizes.daily_limit，0 表示不限）
        if prize.daily_limit > 0:
            today_start = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            won_today = await self.records.count_won_by_prize_since(
                record.activity_id, prize_id, today_start
            )
            if won_today >= prize.daily_limit:
                # 放弃本次中奖：数据库已扣减、Redis 已预扣，两侧都要回补
                return await self._settle_with_refund(
                    record,
                    DrawStatus.REFUNDED,
                    "奖品已达每日中出上限，已回补预扣",
                    prize_id,
                    restore_db_stock=True,
                )

        self.db.add(
            WinRecord(
                draw_record_id=record.id,
                user_id=record.user_id,
                activity_id=record.activity_id,
                prize_id=prize_id,
                prize_type=prize.prize_type,
                prize_name=prize.name,
                prize_image=prize.img_url,
                redemption_code=secrets.token_hex(6).upper(),
                expire_at=datetime.now() + timedelta(days=CLAIM_EXPIRE_DAYS),
            )
        )
        return await self._settle(
            record,
            DrawStatus.WON,
            result_json={
                **jsonable_encoder(payload),
                "prize_name": prize.name,
                "level": prize.prize_level,
            },
        )

    async def _settle_with_refund(
            self,
            record: DrawRecord,
            status: DrawStatus,
            error_message: str,
            prize_id: int,
            restore_db_stock: bool = False,
    ) -> bool:
        """先抢占结算、成功后再回补库存。

        顺序很关键：若先回补再结算，一旦结算因竞态失败（rowcount != 1），
        补偿任务也会回补一次，Redis 计数就会被多补一份。
        """
        settled = await self._settle(record, status, error_message)
        if not settled:
            return False
        if restore_db_stock:
            await self.prizes.increment_remain_stock(prize_id)
        await self.cache.refund_stock(prize_id)
        await self.db.commit()
        return True

    async def _settle(
            self,
            record: DrawRecord,
            status: DrawStatus,
            error_message: str | None = None,
            result_json: dict | None = None,
    ) -> bool:
        """以 status == PENDING 为条件抢占式结算。

        tasks/compensation.py 会把超时仍为 PENDING 的记录置为 FAILED 并回补 Redis
        库存；这里同样以 status == PENDING 为条件更新，保证两边只有一方生效，
        避免出现「库存已回补 + 中奖记录已生成」的重复发放。
        """
        values: dict = {"status": status}
        if error_message is not None:
            values["error_message"] = error_message
        if result_json is not None:
            values["result_json"] = result_json

        claim = await self.db.execute(
            update(DrawRecord)
            .where(
                DrawRecord.id == record.id,
                DrawRecord.status == DrawStatus.PENDING,
            )
            .values(**values)
        )
        if claim.rowcount != 1:
            # 已被补偿任务抢先判定失败：本次不再结算，也不重复回补库存
            await self.db.rollback()
            return False

        await self.db.commit()
        return True

