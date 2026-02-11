from uuid import UUID

from pydantic import BaseModel, Field

from notifications.common.schemas import NotificationChannel


class TemplateBase(BaseModel):
    template_code: str = Field(..., max_length=100)
    locale: str = Field(..., max_length=10)
    channel: NotificationChannel
    subject: str | None = Field(default=None, max_length=255)
    body: str


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    subject: str | None = Field(default=None, max_length=255)
    body: str | None = None


class TemplateRead(TemplateBase):
    id: UUID

    class Config:
        from_attributes = True
