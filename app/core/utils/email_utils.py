import os
import sendgrid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sendgrid.helpers.mail import Mail
from app.core.config import settings


EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER")


def send_email(to_email: str, subject: str, body: str, html=False): 
    if EMAIL_PROVIDER == "mailhog":
        """Send email via SMTP (MailHog or real SMTP)."""
        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        content_type = "html" if html else "plain"
        msg.attach(MIMEText(body, content_type))

        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            if settings.EMAIL_HOST not in ["mailhog", "localhost"]:
                server.starttls()
                if settings.EMAIL_USER and settings.EMAIL_PASSWORD:
                    server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, [to_email], msg.as_string())

        print(f"📤 [SMTP] Email sent to {to_email}")
        return True
    else:
        sg = sendgrid.SendGridAPIClient(api_key=settings.EMAIL_PASSWORD)
        message = Mail(
            from_email=settings.EMAIL_FROM,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body if not html else None,
            html_content=body if html else None,
        )
        try:
            response = sg.send(message)
            print(f"✅ Email sent to {to_email}, status {response.status_code}")
            return True
        except Exception as e:
            print(f"❌ SendGrid API error: {e}")
            return False
