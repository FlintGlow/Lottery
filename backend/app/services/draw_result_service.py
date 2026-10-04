"""抽奖结果落库服务：消费端最终一致性（幂等写入 + MySQL 库存扣减）。"""

from __future__ import annotations

import secrets

from datetime import datetime, timedelta
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.lottery_repository import LotteryRepository
from app.services.lottery_cache import LotteryCacheService
from app.models.lottery import DrawRecord
from app.models.enums import DrawStatus
from app.models import WinRecord
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
            record.status = DrawStatus.NO_PRIZE
            await self.db.flush()
            await self.db.commit()
            return True
        prize = await self.prizes.get(prize_id)
        if prize is None:
            await self.cache.refund_stock(prize_id)
            record.status = DrawStatus.REFUNDED
            record.error_message = "奖品不存在， 已回补Redis预扣"
            await self.db.flush()
            await self.db.commit()
            return True
        #数据库侧原子扣减：仅当 remain_stock > 0 才会成功
        if not await self.prizes.decrement_remain_stock(prize_id):
            # Redis 预扣与 MySQL 库存不一致：回补预扣并标记 REFUNDED
            await self.cache.refund_stock(prize_id)
            record.status = DrawStatus.REFUNDED
            record.error_message = "MySQL库存不足，已回补Redis预扣"
            await self.db.flush()
            await self.db.commit()
            return True

        record.status = DrawStatus.WON
        record.result_json = {
            **jsonable_encoder(payload),
            "prize_name": prize.name,
            "level": prize.prize_level
        }
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
        await self.db.flush()
        await self.db.commit()
        return True

