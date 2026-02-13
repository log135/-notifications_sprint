from functools import lru_cache

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from notifications.common.db import get_db_session
from notifications.common.kafka import KafkaNotificationJobPublisher
from notifications.common.config import settings
from notifications.notifications_api.repositories.templates import TemplateRepository
from notifications.notifications_api.services.notification_service import (
    NotificationService,
)


async def get_db(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncSession:
    return session


def get_template_repository(
    session: AsyncSession = Depends(get_db),
) -> TemplateRepository:
    return TemplateRepository(session=session)


@lru_cache
def get_kafka_publisher() -> KafkaNotificationJobPublisher:
    return KafkaNotificationJobPublisher(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        topic=settings.kafka_outbox_topic,
    )


def get_notification_service(
    publisher: KafkaNotificationJobPublisher = Depends(get_kafka_publisher),
) -> NotificationService:
    return NotificationService(job_publisher=publisher)


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or missing API Key"
        )
    return x_api_key
