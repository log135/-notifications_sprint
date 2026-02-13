from __future__ import annotations

import asyncio
import logging
import httpx

import asyncpg
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError

from notifications.worker.core.config import settings
from notifications.common.retry import retry_async   # добавлен импорт

logger = logging.getLogger(__name__)


async def create_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=2.0)


async def create_db_pool() -> asyncpg.Pool:
    async def _create_pool():
        return await asyncpg.create_pool(
            dsn=settings.db_asyncpg_dsn,
            min_size=1,
            max_size=5,
        )

    pool = await retry_async(
        _create_pool,
        max_attempts=10,
        delay=1,
        exceptions=(OSError, asyncpg.PostgresError),
        logger=logger
    )
    logger.info("Postgres pool created")
    return pool


async def create_kafka_producer() -> AIOKafkaProducer:
    async def _start_producer():
        producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
        try:
            await producer.start()
        except Exception:
            await producer.stop()
            raise
        return producer

    producer = await retry_async(
        _start_producer,
        max_attempts=10,
        delay=1,
        exceptions=(KafkaConnectionError,),
        logger=logger
    )
    logger.info("Kafka producer started (for DLQ)")
    return producer
