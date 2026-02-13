import aiosmtplib
from email.mime.text import MIMEText
from notifications.worker.senders.base import BaseSender
from notifications.common.schemas import NotificationJob


class EmailSender(BaseSender):
    def __init__(self, host: str, port: int, sender: str):
        self.host = host
        self.port = port
        self.sender = sender

    async def send(self, job: NotificationJob, contacts, subject: str, body: str) -> None:
        if not contacts.email:
            raise RuntimeError("User has no email")
        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = contacts.email

        await aiosmtplib.send(
            msg,
            hostname=self.host,
            port=self.port,
            sender=self.sender,
            recipients=[contacts.email],
        )
