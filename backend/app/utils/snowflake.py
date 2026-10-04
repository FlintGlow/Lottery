"""
    雪花算法 ID 生成器
    抽奖流水号 order_no 使用雪花ID, 保证全局唯一、趋势递增, 方便于分库分表与对账
"""

from __future__ import annotations

import threading
import time

from app.core.config import get_settings

_EPOCH = 1704067200000
_WORKER_ID_BITS = 5
_DATACENTER_ID_BITS = 5
_SEQUENCE_BITS = 12

_MAX_WORKER_ID = -1 ^ (-1 << _WORKER_ID_BITS)
_MAX_DATACENTER_ID = -1 ^ (-1 << _DATACENTER_ID_BITS)
_SEQUENCE_MASK = -1 ^ (-1 << _SEQUENCE_BITS)

_WORKER_ID_SHIFT = _SEQUENCE_BITS
_DATACENTER_ID_SHIFT = _SEQUENCE_BITS + _WORKER_ID_BITS
_TIMESTAMP_SHIFT = _SEQUENCE_BITS + _WORKER_ID_BITS + _DATACENTER_ID_BITS


class Snowflake:
    """雪花算法实现"""

    def __init__(self, worker_id: int = 1, datacenter_id: int = 0) -> None:
        if worker_id < 0 or worker_id > _MAX_WORKER_ID:
            raise ValueError(f"worker_id 必须在[0, {_MAX_WORKER_ID}] 之间")
        if datacenter_id < 0 or datacenter_id > _MAX_DATACENTER_ID:
            raise ValueError(f"datacenter_id 必须在 [0, {_MAX_DATACENTER_ID}] 之间")

        self.worker_id = worker_id
        self._datacenter_id = datacenter_id
        self._sequence = 0
        self._last_timestamp = -1
        self._lock = threading.Lock()


    def next_id(self) -> int:
        """生成下一个雪花 ID"""
        with self._lock:
            timestamp = self._current_timestamp()
            if timestamp < self._last_timestamp:
                raise RuntimeError("系统时钟回拨，拒绝生成 ID")

            if timestamp == self._last_timestamp:
                self._sequence = (self._sequence + 1) & _SEQUENCE_MASK
                if self._sequence == 0:
                    timestamp = self._wait_next_millis(self._last_timestamp)
            else:
                self._sequence = 0

            self._last_timestamp = timestamp
            return (
                ((timestamp - _EPOCH) << _TIMESTAMP_SHIFT)
                | (self._datacenter_id << _DATACENTER_ID_SHIFT)
                | (self.worker_id << _WORKER_ID_SHIFT)
                | self._sequence
            )


    def _current_timestamp(self) -> int:
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_timestamp: int) -> int:
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._current_timestamp()
        return timestamp


_settings = get_settings()
_snowflake = Snowflake(
    worker_id = _settings.SNOWFLAKE_WORKER_ID,
    datacenter_id = _settings.SNOWFLAKE_DATACETER_ID
)


def next_id() -> int:
    return _snowflake.next_id()