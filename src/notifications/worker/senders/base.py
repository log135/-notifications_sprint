from __future__ import annotations
from abc import ABC, abstractmethod


class BaseSender(ABC):
    @abstractmethod
    async def send(self, *, to: str, subject: str, body: str) -> None:
        raise NotImplementedError
