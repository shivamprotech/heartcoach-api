import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sendgrid
from sendgrid.helpers.mail import Mail
from app.core.config import settings
from app.core.logging import setup_logger

logger = setup_logger()

EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER")


def send_email(to_email: str, subject: str, body: str, html: bool = False) -> bool:
    """
    Send an email using the configured provider (MailHog via SMTP or SendGrid).

    :param to_email: Recipient email address
    :param subject: Email subject
    :param body: Email body content
    :param html: Whether the body is HTML (default False)
    :return: True if email was sent successfully, False otherwise
    """
    if EMAIL_PROVIDER == "mailhog":
        # -------------------------------------------
        # Send email via SMTP (MailHog or other SMTP)
        # -------------------------------------------
        try:
            msg = MIMEMultipart()
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = to_email
            msg["Subject"] = subject
            content_type = "html" if html else "plain"
            msg.attach(MIMEText(body, content_type))

            # Connect to SMTP server
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                # if settings.EMAIL_HOST not in ["localhost"]:
                #     server.starttls()
                #     if settings.EMAIL_USER and settings.EMAIL_PASSWORD:
                #         server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)

                # Send the email
                server.sendmail(settings.EMAIL_FROM, [to_email], msg.as_string())

            logger.info(f"SMTP Email sent to {to_email}")
            return True

        except Exception as e:
            logger.exception(f"Failed to send SMTP email to {to_email}: {e}")
            return False
    else:
        # -------------------------------------------
        # Send email via SendGrid API
        # -------------------------------------------
        try:
            sg = sendgrid.SendGridAPIClient(api_key=settings.EMAIL_PASSWORD)
            message = Mail(
                from_email=settings.EMAIL_FROM,
                to_emails=to_email,
                subject=subject,
                plain_text_content=body if not html else None,
                html_content=body if html else None,
            )

            response = sg.send(message)
            logger.info(f"SendGrid Email sent to {to_email}, status {response.status_code}")
            return True

        except Exception as e:
            logger.exception(f"SendGrid API error for {to_email}: {e}")
            return False
