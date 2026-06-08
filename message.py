"""Create an AC message (email template) and return its id."""
from ac_client import request

_DEFAULT_FROM_NAME = "Joe Lawrence"
_DEFAULT_EMAIL = "jlawrence@businesscreditworkshop.net"


def create_message(
    subject: str,
    html: str,
    from_name: str = _DEFAULT_FROM_NAME,
    from_email: str = _DEFAULT_EMAIL,
    reply_to: str = _DEFAULT_EMAIL,
) -> str:
    """POST /api/3/messages. Returns the new message id as a string."""
    wrapped_html = (
        f'<div style="font-family: Arial, sans-serif; font-size: 18pt;">'
        f"{html}"
        f"</div>"
    )
    payload = {
        "message": {
            "name": subject,
            "subject": subject,
            "fromemail": from_email,
            "fromname": from_name,
            "replyto": reply_to,
            "mime": "html",
            "body": wrapped_html,
        }
    }
    _, body = request("POST", "/api/3/messages", json=payload)
    return str(body["message"]["id"])
