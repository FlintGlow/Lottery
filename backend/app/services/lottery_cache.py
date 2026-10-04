"""抽奖热点缓存：奖品权重 Hash + 库存 String + 原子预扣/防重锁 Lua。"""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models.enums import PrizeStatus
from app.models.prize import Prize
from app.repositories.prize_repository import PrizeRepository

_DEDUCT_SCRIPT = """
local stock = tonumber(redis.call('GET', KEYS[1]) or '-1')
if stock <= 0 then
    return -1
end
return redis.call('DECR', KEYS[1])
"""

_RELEASE_LOCK_SCRIPT = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
else
    return 0
end
"""

@dataclass(frozen=True)
class PrizeCandidate:
    """可参与抽奖的候选奖品"""

    prize_id: int
    name: str
    weight: int


class LotteryCacheService:
    """管理抽奖相关 Redis键（权重缓存、库存预扣、防重锁）"""

    PRIZES_KEY = "lottery:prizes:{activity_id}"
    STOCK_KEY = "lottery:stock:{prize_id}"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.prizes = PrizeRepository(db)

    async def warm_activity(self, activity_id: int) -> None:
        """活动发布/奖品变更后，从 DB 重建权重缓存与库存键。"""
        items: list[Prize] = []
        page: int = 1
        while True:
            batch, _ =await self.prizes.list_prizes(
                activity_id=activity_id,
                status=PrizeStatus.ENABLED,
                page=page,
                page_size=200,
            )
            items.extend(batch)
            if len(batch) < 200:
                break
            page += 1

        redis = await get_redis()
        prizes_key = self.PRIZES_KEY.format(activity_id=activity_id)
        mapping: dict[str, str] = {}
        for prize in items:
            if prize.weight > 0 and prize.status == PrizeStatus.ENABLED:
                mapping[str(prize.id)] = json.dumps(
                    {"id": prize.id, "name": prize.name, "weight": prize.weight},
                    ensure_ascii=False,
                )
            await self._ensure_stock(prize)
        if mapping:
            await redis.hset(prizes_key,mapping=mapping)
        else:
            await redis.delete(prizes_key)

    async def load_candidates(self, activity_id: int) -> list[PrizeCandidate]:
        """读取候选奖品（权重>0 且 Redis 库存>0）；缓存缺失时回源 DB 预热。"""
        redis = await get_redis()
        prizes_key = self.PRIZES_KEY.format(activity_id=activity_id)
        raw = await redis.hgetall(prizes_key)
        if not raw:
            await self.warm_activity(activity_id)
            raw = await redis.hgetall(prizes_key)

        candidates: list[PrizeCandidate] = []
        for prize_id_str, data in raw.items():
            info = json.loads(data)
            stock = await self.get_stock_or_init(int(prize_id_str))
            if stock > 0:
                candidates.append(
                    PrizeCandidate(
                        prize_id=int(prize_id_str),
                        name=info["name"],
                        weight=int(info["weight"]),
                    )
                )
        return candidates

    async def get_stock_or_init(self, prize_id: int) -> int:
        """读取库存；键缺失时以 DB remain_stock 初始化。"""
        redis = await get_redis()
        key = self.STOCK_KEY.format(prize_id=prize_id)
        value = await redis.get(key)
        if value is not None:
            return int(value)
        prize = await self.prizes.get(prize_id)
        if prize is None:
            return -1
        await redis.set(key, prize.remain_stock)
        return prize.remain_stock

    async def deduct_stock(self, prize_id: int) -> int:
        """Lua 原子预扣库存， 返回减扣后库存， 无货返回 -1"""
        redis = await get_redis()
        key = self.STOCK_KEY.format(prize_id=prize_id)
        return int(await redis.eval(_DEDUCT_SCRIPT, 1, key))

    async def refund_stock(self, prize_id: int) -> int:
        """库存回补,键不存在时按照数据库值重建， 避免把库存错写成1 """
        redis = await get_redis()
        key = self.STOCK_KEY.format(prize_id=prize_id)
        if await redis.exists(key):
            return int(await redis.incr(key))

        prize = await self.prizes.get(prize_id)
        if prize is None:
            return -1
        restored = prize.remain_stock + 1
        await redis.set(key, restored)
        return restored

    async def set_stock(self,prize_id: int, stock: int) -> None:
        redis = await get_redis()
        await redis.set(self.STOCK_KEY.format(prize_id=prize_id), stock)

    async def remove_stock(self, prize_id: int) -> None:
        redis = await get_redis()
        await redis.delete(self.STOCK_KEY.format(prize_id=prize_id))

    async def invalidate_activity(self, activity_id: int) -> None:
        """奖品变更后失效权重缓存（下次抽奖重建）"""
        redis = await get_redis()
        await redis.delete(self.PRIZES_KEY.format(activity_id=activity_id))

    async def release_lock(self, key: str, token: str) -> None:
        """Lua 校验令牌后释放防重锁，防止误删他人锁。"""
        redis = await get_redis()
        await redis.eval(_RELEASE_LOCK_SCRIPT, 1, key, token)

    async def _ensure_stock(self, prize: Prize) -> None:
        redis = await get_redis()
        key = self.STOCK_KEY.format(prize_id=prize.id)
        if await redis.exists(key) ==0:
            await redis.set(key, prize.remain_stock)







