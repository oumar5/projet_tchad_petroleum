"""RabbitMQ event publisher (aio_pika async)."""
import json
from typing import Any

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message


class EventPublisher:
    def __init__(self, amqp_url: str, exchange_name: str = "smartbarrel.events"):
        self._amqp_url = amqp_url
        self._exchange_name = exchange_name
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._amqp_url)
        channel = await self._connection.channel()
        self._exchange = await channel.declare_exchange(
            self._exchange_name, ExchangeType.TOPIC, durable=True
        )

    async def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        if self._exchange is None:
            raise RuntimeError("Publisher not connected. Call connect() first.")
        message = Message(
            body=json.dumps(payload, default=str).encode(),
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
        )
        await self._exchange.publish(message, routing_key=routing_key)

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
