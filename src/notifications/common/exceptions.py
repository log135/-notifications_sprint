class NotificationServiceError(Exception):
    pass


class EventNotSupportedError(NotificationServiceError):
    def __init__(self, event_type: str):
        self.event_type = event_type
        super().__init__(f"Event type '{event_type}' is not supported in this MVP")


class UnknownEventTypeError(NotificationServiceError):
    def __init__(self, event_type: str):
        self.event_type = event_type
        super().__init__(f"Unknown event type: '{event_type}'")


class InvalidEventDataError(NotificationServiceError):
    def __init__(self, context: str, detail: str):
        self.context = context
        self.detail = detail
        super().__init__(f"Invalid payload for {context}: {detail}")


class TemplateNotFoundError(NotificationServiceError):
    def __init__(self, template_id: str):
        self.template_id = template_id
        super().__init__(f"Template with id '{template_id}' not found")


# class NotificationSendError(NotificationServiceError):
#     """Ошибка отправки уведомления через внешний сервис."""
#     pass
