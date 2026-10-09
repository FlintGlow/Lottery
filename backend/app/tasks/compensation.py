"""补偿任务：发件箱重发 + PENDING 记录对账回补"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import or_, select, update

from app.core.rabbitmq import publish_message
from app.core.database import AsyncSessionLocal
from app.models.enums import DrawStatus, OutboxStatus
from app.models.lottery import DrawRecord
from app.models.outbox import MessageOutbox
from app.repositories.message_outbox_repository import MessageOutboxRepository
from app.services.lottery_cache import LotteryCacheService

logger = logging.getLogger(__name__)

COMPENSATION_INTERVAL_SECONDS = 60
BATCH_SIZE = 50
PENDING_TIMEOUT_MINUTES = 5
MAX_OUTBOX_RETRY = 10          # 发件箱最大重试次数，超过则置为 FAILED 不再重发

async def run_compensation_loop() -> None:
    """周期性执行补偿任务"""
    while True:
        try:
            await compensate_outbox()
            await compensate_pending_records()
        except Exception:
            logger.exception("补偿任务执行失败")
        await asyncio.sleep(COMPENSATION_INTERVAL_SECONDS)

async def compensate_outbox() -> None:
    """重发 PENDING 且到期的发件箱消息"""
    now = datetime.now()
    async with AsyncSessionLocal() as session:
        stmt = (
            select(MessageOutbox)
            .where(
                MessageOutbox.status == OutboxStatus.PENDING,
                or_(
                    MessageOutbox.next_retry_at.is_(None),
                    MessageOutbox.next_retry_at <= now,
                ),
            )
            .order_by(MessageOutbox.id)
            .limit(BATCH_SIZE)
        )
        rows = (await session.execute(stmt)).scalars().all()
        for message in rows:
            try:
                await publish_message(message.exchange, message.routing_key, message.payload)
                message.status = OutboxStatus.SENT
                message.last_error = None
            except Exception as exc:
                message.retry_count += 1
                # 记录真实的异常类型与内容
                message.last_error = f"{type(exc).__name__}: {exc}"[:255]
                if message.retry_count >= MAX_OUTBOX_RETRY:
                    message.status = OutboxStatus.FAILED
                    message.next_retry_at = None
                else:
                    message.next_retry_at = now + timedelta(
                        seconds=min(2 ** message.retry_count, 300)
                    )
        if rows:
            await session.commit()
            logger.info("发件箱补偿完成：处理 %s 条", len(rows))

async def compensate_pending_records() -> None:
    """对账：长时间 PENDING 的记录回补 Redis 库存并标记 FAILED"""
    threshold = datetime.now() - timedelta(minutes=PENDING_TIMEOUT_MINUTES)
    async with AsyncSessionLocal() as session:
        stmt = (
            select(DrawRecord)
            .where(
                DrawRecord.status == DrawStatus.PENDING,
                DrawRecord.created_at < threshold,
            )
            .order_by(DrawRecord.id)
            .limit(BATCH_SIZE)
        )
        rows = (await session.execute(stmt)).scalars().all()
        cache = LotteryCacheService(session)
        for record in rows:
            #   用条件更新抢占，避免与消费者重复处理
            updated = await session.execute(
                update(DrawRecord)
                .where(
                   DrawRecord.id == record.id,
                   DrawRecord.status == DrawStatus.PENDING,     #只处理    PENDING
                )
                .values(status=DrawStatus.FAILED, error_message= "处理超时，已回补库存" )
            )
            if updated.rowcount != 1:
                continue            #消费者已抢先落库， 跳过
            if record.prize_id is not None:
                await cache.refund_stock(record.prize_id)   #先改状态再回补
        if rows:
            await session.commit()
            logger.info("PENDING 记录补偿完成： 处理 %s条", len(rows))