from uuid import UUID
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from notifications.notifications_api.main import app
from notifications.notifications_api.utils.dependencies import (
    get_template_repository,
    get_notification_service,
    get_kafka_publisher,
)
from notifications.notifications_api.schemas.template import (
    TemplateCreate,
    TemplateRead,
)


class FakeTemplateRepo:
    def __init__(self) -> None:
        self._items: list[TemplateRead] = []

    async def create(self, template_in: TemplateCreate) -> TemplateRead:
        for existing in self._items:
            if (
                existing.template_code == template_in.template_code
                and existing.locale == template_in.locale
                and existing.channel == template_in.channel
            ):
                raise IntegrityError("duplicate template", params=None, orig=None)

        tpl = TemplateRead(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            template_code=template_in.template_code,
            locale=template_in.locale,
            channel=template_in.channel,
            subject=template_in.subject,
            body=template_in.body,
        )
        self._items.append(tpl)
        return tpl

    async def list(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[TemplateRead]:
        return self._items[offset : offset + limit]


class FakeNotificationService:
    async def handle_event(self, event) -> int:
        return 1


class FakeKafkaPublisher:
    def __init__(self):
        self.start = AsyncMock()
        self.stop = AsyncMock()
        self.publish_job = AsyncMock()
        self.is_ready = AsyncMock(return_value=True)


@pytest.fixture(autouse=True)
def set_test_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-api-key")
    from notifications.common.config import settings

    settings.api_key = "test-api-key"
    yield


@pytest.fixture(autouse=True)
def override_dependencies():
    fake_repo = FakeTemplateRepo()
    fake_service = FakeNotificationService()
    fake_publisher = FakeKafkaPublisher()

    app.dependency_overrides[get_template_repository] = lambda: fake_repo
    app.dependency_overrides[get_notification_service] = lambda: fake_service
    app.dependency_overrides[get_kafka_publisher] = lambda: fake_publisher

    yield

    app.dependency_overrides.clear()


@pytest.fixture
def api_client() -> TestClient:
    client = TestClient(app)
    client.headers.update({"X-API-Key": "test-api-key"})
    return client
