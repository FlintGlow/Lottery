"""MQ出站消息仓储"""

from __future__ import annotations

from app.models.outbox import MessageOutbox
from app.repositories.base import BaseRepository

class MessageOutboxRepository(BaseRepository[MessageOutbox]):
    model = MessageOutbox