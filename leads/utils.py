from twilio.rest import Client
from django.conf import settings
settings.TWILIO_SID
settings.TWILIO_TOKEN
settings.TWILIO_WHATSAPP_FROM
settings.COUNSELLOR_WHATSAPP


def send_whatsapp_to_counsellor(summary_text):
    client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
    message = client.messages.create(
        body=summary_text,
        from_="whatsapp:+14155238886",
        to="whatsapp:+917605021990" 
    )
