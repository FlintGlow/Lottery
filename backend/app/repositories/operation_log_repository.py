"""操作日志的仓储"""

from __future__ import annotations

from app.models.log import OperationLog

from app.repositories.base import BaseRepository


class OperationLogRepository(BaseRepository[OperationLog]):
    model = OperationLog

