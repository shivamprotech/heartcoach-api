# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_phone = os.getenv("PHONE_FROM")
client = Client(account_sid, auth_token)


def send_phone(to_phone: str, body: str):
    try:
        message = client.messages.create(
            body=body,
            from_=from_phone,
            to=to_phone,
        )
        print(f"✅ SMS sent to {to_phone}")
        return True
    except Exception as e:
        print(f"❌ Twilio API error: {e}")
        return False
