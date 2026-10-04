"""抽奖结果异步消费者： 手动ACK、 进程内重试、最终失败进死信队列"""

from __future__ import annotations

import asyncio
import json
import logging

from aio_pika import IncomingMessage
from aio_pika.abc import AbstractRobustChannel

from app.core.config import get_settings
from app.core.rabbitmq import ensure_topology, get_rabbitmq
from app.core.database import AsyncSessionLocal
from app.services.draw_result_service import DrawResultService

logger = logging.getLogger(__name__)
settings = get_settings()

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2

async def consume_draw_results() -> None:
    """消费抽奖结果消息（常驻任务）"""
    connection = await get_rabbitmq()
    channel: AbstractRobustChannel = await connection.channel()
    await channel.set_qos(prefetch_count=10)
    await ensure_topology(channel)
    queue = await channel.get_queue(settings.DRAW_QUEUE)
    await queue.consume(_handle_message)
    logger.info("抽奖消费者已启用，队列：%s", settings.DRAW_QUEUE)
    await asyncio.Future()


async def _handle_message(message: IncomingMessage) -> None:
    """手动ACK，处理失败重试，最终失败 nack（requeue = False） 进死信队列"""
    async with message.process(requeue = False):
        payload = json.loads(message.body.decode("utf-8"))
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with AsyncSessionLocal() as session:
                    await DrawResultService(session).persist(payload)
                return
            except Exception:
                logger.exception(
                    "抽奖落库失败 order_no = %s attempt = %s/%s",
                    payload.get("order_no"),
                    attempt,
                    MAX_RETRIES,
                )
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
                else:
                    raise   #最终失败 消息进入死信队列