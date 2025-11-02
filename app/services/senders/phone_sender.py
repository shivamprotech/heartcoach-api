# app/services/senders/email_sender.py
import anyio
from app.core.config import settings
from app.core.utils.phone_utils import send_phone as sync_send_phopne


class PhoneSender:
    def __init__(self, from_phone: str | None = None):
        self.from_phone = from_phone or settings.PHONE_FROM

    async def send_phone(self, to_phone: str, body: str) -> bool:
        """
        Wraps the existing sync `send_email` helper into a non-blocking call.
        Replace this implementation with an async SendGrid client later for better performance.
        """
        # call sync function in threadpool to avoid blocking the event loop
        try:
            result = await anyio.to_thread.run_sync(sync_send_phopne, to_phone, body)
            return bool(result)
        except Exception as e:
            # you can also emit structured logs here
            print("Error sending email (async wrapper):", e)
            return False
