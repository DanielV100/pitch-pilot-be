import resend
from app.core.config import settings

resend.api_key = settings.RESEND_API_KEY


VERIFY_TEMPLATE = """
Hi {username},

Welcome to PitchPilot! Click the link below to verify your account:

{verification_url}

If you didn't request this, please ignore this email.

– PitchPilot Team
"""

async def send_verification_email(user, token: str) -> None:
    """
    Dispatch a confirmation e-mail via Resend that feels right at home in the PitchPilot cockpit.
    """
    verification_url = f"{settings.FRONTEND_URL}/verify?token={token}"
    body = VERIFY_TEMPLATE.format(username=user.username, verification_url=verification_url)

    params: resend.Emails.SendParams = {
       "from": settings.RESEND_SENDER_MAIL,
        "to": [user.email],
        "subject": "PitchPilot – Confirm Pre-Flight Check",
        "html": body,
    }

    resend.Emails.send(params)
