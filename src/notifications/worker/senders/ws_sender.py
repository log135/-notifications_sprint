from __future__ import annotations
import logging

from notifications.worker.senders.base import BaseSender
from notifications.common.schemas import NotificationJob

logger = logging.getLogger(__name__)


class WsSender(BaseSender):
    async def send(self, job: NotificationJob, contacts, subject: str, body: str) -> None:
        if not contacts.ws_session_id:
            raise RuntimeError("User has no ws session id")

        logger.info(
            "[WS] Sending to session=%s subject=%r body=%r",
            contacts.ws_session_id,
            subject,
            body,
        )
