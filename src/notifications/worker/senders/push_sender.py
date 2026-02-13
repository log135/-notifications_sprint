from __future__ import annotations
import logging

from notifications.worker.senders.base import BaseSender
from notifications.common.schemas import NotificationJob

logger = logging.getLogger(__name__)


class PushSender(BaseSender):
    async def send(self, job: NotificationJob, contacts, subject: str, body: str) -> None:
        if not contacts.push_token:
            raise RuntimeError("User has no push token")

        logger.info(
            "[PUSH] Sending to=%s subject=%r body=%r",
            contacts.push_token,
            subject,
            body,
        )
