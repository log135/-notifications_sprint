from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from notifications.common.exceptions import (
    EventNotSupportedError,
    UnknownEventTypeError,
)
from notifications.common.kafka import KafkaNotificationJobPublisher
from notifications.common.schemas import (
    NotificationChannel,
    NotificationJob,
    NotificationMeta,
)
from notifications.notifications_api.schemas.event import (
    Event,
    UserRegisteredEvent,
    NewFilmReleasedEvent,
    CampaignTriggeredEvent,
)


class NotificationService:
    def __init__(self, job_publisher: KafkaNotificationJobPublisher) -> None:
        self._job_publisher = job_publisher

    async def handle_event(self, event: Event) -> int:
        jobs = self._map_event_to_jobs(event)

        for job in jobs:
            await self._job_publisher.publish_job(job.model_dump(mode="json"))

        return len(jobs)

    def _map_event_to_jobs(self, event: Event) -> List[NotificationJob]:
        now = datetime.now(timezone.utc)

        match event:
            case UserRegisteredEvent():
                return self._map_user_registered(event, now)
            case NewFilmReleasedEvent():
                raise EventNotSupportedError(event.event_type.value)
            case CampaignTriggeredEvent():
                raise EventNotSupportedError(event.event_type.value)
            case _:
                raise UnknownEventTypeError(str(event.event_type))

    def _map_user_registered(
        self, event: UserRegisteredEvent, now: datetime
    ) -> List[NotificationJob]:
        payload = event.payload

        job = NotificationJob(
            job_id=uuid4(),
            user_id=payload.user_id,
            channel=NotificationChannel.EMAIL,
            template_code="welcome_email",
            locale=payload.locale,
            data={
                "registration_channel": payload.registration_channel,
                "user_agent": payload.user_agent,
            },
            meta=NotificationMeta(
                event_type=event.event_type.value,
                event_id=event.event_id,
                campaign_id=None,
            ),
            created_at=now,
        )
        return [job]

    def _map_new_film_released(self, event: NewFilmReleasedEvent) -> List[NotificationJob]:
        raise EventNotSupportedError(event.event_type.value)

    def _map_campaign_triggered(self, event: CampaignTriggeredEvent) -> List[NotificationJob]:
        raise EventNotSupportedError(event.event_type.value)
