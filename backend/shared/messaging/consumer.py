"""RabbitMQ event consumer."""
import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

import aio_pika
from aio_pika import ExchangeType


class EventConsumer:
    def __init__(self, amqp_url: str, queue_name: str, routing_keys: list[str],
                 exchange_name: str = "smartbarrel.events"):
        self._amqp_url = amqp_url
        self._queue_name = queue_name
        self._routing_keys = routing_keys
        self._exchange_name = exchange_name
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None

    async def consume(self, handler: Callable[[str, dict[str, Any]], Awaitable[None]]) -> None:
        self._connection = await aio_pika.connect_robust(self._amqp_url)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=10)
        exchange = await channel.declare_exchange(
            self._exchange_name, ExchangeType.TOPIC, durable=True
        )
        queue = await channel.declare_queue(self._queue_name, durable=True)
        for rk in self._routing_keys:
            await queue.bind(exchange, routing_key=rk)

        async with queue.iterator() as it:
            async for message in it:
                async with message.process(requeue=False):
                    payload = json.loads(message.body.decode())
                    await handler(message.routing_key or "", payload)

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()


async def run_consumer_forever(consumer: EventConsumer,
                               handler: Callable[[str, dict[str, Any]], Awaitable[None]]) -> None:
    while True:
        try:
            await consumer.consume(handler)
        except Exception:
            await asyncio.sleep(5)
