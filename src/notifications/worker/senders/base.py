from __future__ import annotations
from abc import ABC, abstractmethod
from notifications.common.schemas import NotificationJob


class BaseSender(ABC):
    @abstractmethod
    async def send(self, job: NotificationJob, contacts, subject: str, body: str) -> None:
        raise NotImplementedError
