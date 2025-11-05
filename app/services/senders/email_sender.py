import anyio
import anyio.to_thread
from app.core.config import settings
from app.core.utils.email_utils import send_email as sync_send_email
from app.core.logging import setup_logger

logger = setup_logger()


class EmailSender:
    def __init__(self, from_email: str | None = None):
        """
        Initialize EmailSender with a default sender email.

        :param from_email: Optional sender email address. Defaults to settings.EMAIL_FROM.
        """
        self.from_email = from_email or settings.EMAIL_FROM

    async def send_email(self, to_email: str, subject: str, body: str, html: bool = False) -> bool:
        """
        Send an email asynchronously by wrapping a synchronous email function.

        This method wraps the existing synchronous `send_email` helper in a thread
        using `anyio.to_thread.run_sync` to avoid blocking the FastAPI async event loop.
        In the future, it can be replaced by a fully async email client (e.g., SendGrid, SMTP async).

        :param to_email: Recipient email address.
        :param subject: Email subject.
        :param body: Email body content (plain text or HTML depending on `html`).
        :param html: Whether the body is HTML (default False).
        :return: True if the email was sent successfully, False otherwise.
        :rtype: bool
        """
        try:
            logger.info(f"Sending email to {to_email} with subject: '{subject}'")

            result = await anyio.to_thread.run_sync(sync_send_email, to_email, subject, body, html)

            if result:
                logger.info(f"Email successfully sent to {to_email}")
            else:
                logger.error(f"Failed to send email to {to_email}")

            return bool(result)

        except Exception as e:
            logger.exception(f"Exception occurred while sending email to {to_email}: {e}")
            return False
