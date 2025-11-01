# app/services/senders/email_sender.py
import anyio
from app.core.config import settings
from app.core.utils.email_utils import send_email as sync_send_email


class EmailSender:
    def __init__(self, from_email: str | None = None):
        self.from_email = from_email or settings.EMAIL_FROM

    async def send_email(self, to_email: str, subject: str, body: str, html: bool = False) -> bool:
        """
        Wraps the existing sync `send_email` helper into a non-blocking call.
        Replace this implementation with an async SendGrid client later for better performance.
        """
        # call sync function in threadpool to avoid blocking the event loop
        try:
            result = await anyio.to_thread.run_sync(sync_send_email, to_email, subject, body, html)
            return bool(result)
        except Exception as e:
            # you can also emit structured logs here
            print("Error sending email (async wrapper):", e)
            return False
