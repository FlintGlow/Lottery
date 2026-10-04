from __future__ import annotations

import json

from aio_pika import DeliveryMode, ExchangeType, Message, connect_robust
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel

from app.core.config import get_settings

settings = get_settings()

_connection: AbstractRobustConnection | None = None

async def get_rabbitmq() -> AbstractRobustConnection:
    """获取 RabbitMQ 连接（懒加载单例，断线自动重连）。"""
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL, reconnect_interval=2)
    return _connection


async def close_rabbitmq() -> None:
    """应用关闭时释放连接。"""
    global _connection
    if _connection is not None and not _connection.is_closed:
        await _connection.close()
        _connection = None


async def publish_message(exchange_name: str,routing_key: str, payload:dict) -> None:
    """发布持久化消息（publisher confirm），发布前确保拓扑就绪。"""
    connection = await get_rabbitmq()
    channel: AbstractRobustChannel = await connection.channel(publisher_confirm=True)
    try:
        await ensure_topology(channel)
        exchange = await channel.get_exchange(exchange_name)
        message = Message(
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key)
    finally:
        await channel.close()


async def ensure_topology(channel: AbstractRobustChannel) -> None:
    """声明交换机、主队列（带 DLX）与死信队列，并完成绑定。

        生产端与消费端共用，保证队列参数一致（否则重复声明会 406）。
    """
    exchange = await channel.declare_exchange(
        settings.DRAW_EXCHANGE,
        ExchangeType.TOPIC,
        durable=True,
    )
    dlx = await channel.declare_exchange(
        settings.DRAW_DLX,
        ExchangeType.DIRECT,
        durable=True,
    )
    main_queue = await channel.declare_queue(
        settings.DRAW_QUEUE,
        durable=True,
        arguments={
            "x-dead-letter-exchange": settings.DRAW_DLX,
            "x-dead-letter-routing-key": settings.DRAW_DLQ,
        },
    )
    await main_queue.bind(exchange, settings.DRAW_QUEUE)
    dead_queue = await channel.declare_queue(
        settings.DRAW_DLQ,
        durable=True,
    )
    await dead_queue.bind(dlx, settings.DRAW_DLQ)



















