from __future__ import annotations

import logging

from jinja2 import UndefinedError

from notifications.common.config import Settings
from notifications.common.schemas import (
    NotificationChannel,
    NotificationJob,
    NotificationStatus,
)

from notifications.worker.auth import AuthClient
from notifications.worker.dlq import DlqPublisher
from notifications.worker.repositories import (
    NotificationDeliveryRepository,
    TemplateRepository,
)
from notifications.worker.senders import EmailSender, PushSender, WsSender
from notifications.worker.processor.retry_engine import attempt_with_retries
from notifications.worker.processor.timing import (
    handle_expiration_if_needed,
    wait_send_after_if_needed,
)
from notifications.worker.core.template_renderer import render_html_template

logger = logging.getLogger(__name__)


class JobProcessor:
    def __init__(
        self,
        settings: Settings,
        template_repo: TemplateRepository,
        delivery_repo: NotificationDeliveryRepository,
        auth_client: AuthClient,
        email_sender: EmailSender,
        push_sender: PushSender,
        ws_sender: WsSender,
        dlq_publisher: DlqPublisher,
    ) -> None:
        self.settings = settings
        self.template_repo = template_repo
        self.delivery_repo = delivery_repo
        self.auth_client = auth_client
        self.email_sender = email_sender
        self.push_sender = push_sender
        self.ws_sender = ws_sender
        self.dlq = dlq_publisher

        self._senders = {
            NotificationChannel.EMAIL: email_sender,
            NotificationChannel.PUSH: push_sender,
            NotificationChannel.WS: ws_sender,
        }

    async def handle_job(self, job: NotificationJob) -> None:
        existing = await self._get_existing(job)
        if self._should_skip(existing):
            return

        expired = await handle_expiration_if_needed(
            job=job,
            existing=existing,
            delivery_repo=self.delivery_repo,
        )
        if expired:
            return

        await wait_send_after_if_needed(
            job=job,
            max_send_delay_seconds=self.settings.max_send_delay_seconds,
        )

        existing_attempts = existing.attempts if existing else 0
        await attempt_with_retries(
            job=job,
            existing_attempts=existing_attempts,
            max_attempts=self.settings.max_attempts,
            retry_delays=self.settings.retry_delays_seconds,
            attempt_send_fn=self._attempt_send,
            delivery_repo=self.delivery_repo,
            dlq_publisher=self.dlq,
        )

    async def _get_existing(self, job: NotificationJob):
        return await self.delivery_repo.get_by_job_id(job.job_id)

    def _should_skip(self, existing) -> bool:
        if not existing:
            return False

        if existing.status == NotificationStatus.SENT.value:
            logger.info("Job %s already SENT - skipping", existing.job_id)
            return True

        if (
            existing.status
            in (NotificationStatus.EXPIRED.value, NotificationStatus.FAILED.value)
            and existing.attempts >= self.settings.max_attempts
        ):
            logger.info(
                "Job %s already final (%s, attempts=%s) - skipping",
                existing.job_id,
                existing.status,
                existing.attempts,
            )
            return True

        return False

    @staticmethod
    def _normalize_channel(channel: NotificationChannel | str) -> str:
        if isinstance(channel, NotificationChannel):
            return channel.value
        return str(channel)

    async def _attempt_send(self, job: NotificationJob) -> None:
        contacts = await self.auth_client.get_user_contacts(job.user_id)

        channel_str = self._normalize_channel(job.channel)
        template = await self.template_repo.get_template(
            template_code=job.template_code,
            locale=job.locale,
            channel=channel_str,
        )
        if not template:
            raise RuntimeError(
                f"Template not found: code={job.template_code} "
                f"locale={job.locale} channel={channel_str}"
            )

        subject_template = template.subject or ""
        body_template = template.body or ""

        try:
            subject = render_html_template(subject_template, job.data)
            body = render_html_template(body_template, job.data)
        except UndefinedError as e:
            raise RuntimeError(f"Missing variable in template: {e}") from e

        sender = self._senders.get(job.channel)
        if sender is None:
            raise RuntimeError(f"Unsupported channel: {job.channel}")

        await sender.send(job=job, contacts=contacts, subject=subject, body=body)
