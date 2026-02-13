import asyncio
import json
import logging
from typing import Any, Dict, Optional

from aiokafka import AIOKafkaProducer, errors

from notifications.common.retry import retry_async

logger = logging.getLogger(__name__)


class KafkaNotificationJobPublisher:
    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._producer: Optional[AIOKafkaProducer] = None
        self._enabled: bool = True

    async def start(self) -> None:
        if self._producer is not None or not self._enabled:
            return

        max_attempts = 10
        delay_seconds = 1

        async def _start_producer():
            producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            )
            try:
                await producer.start()
            except Exception:
                try:
                    await producer.stop()
                except Exception:
                    logger.exception("Producer stop failed after unsuccessful start")
                raise
            return producer

        try:
            producer = await retry_async(
                _start_producer,
                max_attempts=max_attempts,
                delay=delay_seconds,
                exceptions=(Exception,),
                logger=logger
            )
            self._producer = producer
            self._enabled = True
            logger.info(
                "Kafka producer started bootstrap_servers=%s", self._bootstrap_servers
            )
        except Exception:
            logger.error(
                "Kafka producer is unavailable after %s attempts; switching to degraded mode",
                max_attempts,
            )
            self._enabled = False
            self._producer = None

    def is_ready(self) -> bool:
        return self._enabled and self._producer is not None

    async def stop(self) -> None:
        if self._producer is None:
            return
        try:
            await self._producer.stop()
        except Exception:
            logger.exception("Failed to stop Kafka producer")
        finally:
            self._producer = None

    async def publish_job(self, payload: Dict[str, Any]) -> None:
        if not self._enabled or self._producer is None:
            logger.info(
                "Kafka degraded mode: would publish topic=%s payload=%s",
                self._topic,
                payload,
            )
            return

        try:
            await self._producer.send_and_wait(self._topic, payload)
        except errors.KafkaError:
            logger.exception("Kafka error while publishing topic=%s", self._topic)
        except Exception:
            logger.exception("Unexpected error while publishing topic=%s", self._topic)
