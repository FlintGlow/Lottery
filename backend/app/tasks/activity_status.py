"""活动状态推进任务"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from app.core.database import AsyncSessionLocal
from app.repositories.activity_repository import ActivityRepository

logger = logging.getLogger(__name__)

ACTIVITY_STATUS_INTERVAL_SECONDS = 5


async def advance_activity_status() -> None:
    """批量推进一次活动状态"""
    async with AsyncSessionLocal() as session:
        repository = ActivityRepository(session)
        ended_count, ongoing_count = await repository.advance_statuses(datetime.now())
        if ended_count or ongoing_count:
            logger.info(
                "活动状态推进完成：进行中 %s 条，已结束 %s 条",
                ongoing_count,
                ended_count,
            )


async def run_activity_status_loop() -> None:
    while True:
        try:
            await advance_activity_status()
        except Exception:
            logger.exception("活动状态推进任务执行失败")

        await asyncio.sleep(ACTIVITY_STATUS_INTERVAL_SECONDS)