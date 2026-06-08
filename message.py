"""Create an AC message (email template) and return its id."""
import re
import html as _html_mod
from ac_client import request

_DEFAULT_FROM_NAME = "Joe Lawrence"
_DEFAULT_EMAIL = "jlawrence@businesscreditworkshop.net"


def _to_plain_text(html_content: str) -> str:
    """Strip HTML tags and unescape entities to produce a plain-text fallback."""
    no_tags = re.sub(r"<[^>]+>", " ", html_content)
    return re.sub(r" {2,}", " ", _html_mod.unescape(no_tags)).strip()


def create_message(
    subject: str,
    html: str,
    from_name: str = _DEFAULT_FROM_NAME,
    from_email: str = _DEFAULT_EMAIL,
    reply_to: str = _DEFAULT_EMAIL,
) -> str:
    """
    POST /api/3/messages. Returns the new message id as a string.
    After creation, GETs the message back and asserts html is non-empty.
    Raises loudly if html_empty is true or subject was mangled.
    """
    payload = {
        "message": {
            "name": subject,
            "subject": subject,
            "fromemail": from_email,
            "fromname": from_name,
            "reply2": reply_to,          # AC v3 field (not "replyto")
            "html": html,                # AC v3 field (not "body")
            "text": _to_plain_text(html),
        }
    }
    _, body = request("POST", "/api/3/messages", json=payload)
    message_id = str(body["message"]["id"])

    # Verify the message stored correctly
    _, get_body = request("GET", f"/api/3/messages/{message_id}")
    msg = get_body.get("message", {})

    if msg.get("html_empty") or not msg.get("html"):
        raise RuntimeError(
            f"Message {message_id} has empty HTML body after creation — "
            f"html_empty={msg.get('html_empty')}, html={msg.get('html')!r}"
        )

    stored_subject = msg.get("subject", "")
    print(f"Message {message_id} verified: html non-empty, subject={stored_subject!r}")
    if stored_subject != subject:
        raise RuntimeError(
            f"Subject mismatch after creation — "
            f"sent={subject!r}, stored={stored_subject!r}"
        )

    return message_id
