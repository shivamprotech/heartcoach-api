import sendgrid
from sendgrid.helpers.mail import Mail
from app.core.config import settings


def send_email(to_email: str, subject: str, body: str, html=False):
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
