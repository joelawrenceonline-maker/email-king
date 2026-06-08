"""Send the morning draft-reminder nudge to me only, via Resend API."""
import os
import json
import urllib.request

_SUBJECT = "Time to write today's BCW email"
_RESEND_URL = "https://api.resend.com/emails"


def send_morning_nudge() -> None:
    """
    Send a plain-text reminder to NUDGE_TO via Resend.
    This is the ONLY thing in this service that sends an email,
    and it sends only to a single personal address — never to a list.
    """
    api_key = os.environ["RESEND_API_KEY"]
    nudge_from = os.environ["NUDGE_FROM"]
    nudge_to = os.environ["NUDGE_TO"]
    draft_link = os.environ["DRAFT_LINK"]

    body_text = f"Time to start today's BCW email. Jump into your drafting project here:\n{draft_link}\n"

    payload = json.dumps({
        "from": nudge_from,
        "to": [nudge_to],
        "subject": _SUBJECT,
        "text": body_text,
    }).encode()

    req = urllib.request.Request(
        _RESEND_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "email-king/0.2 (python-urllib)",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"[RESEND ERROR] HTTP {e.code}: {error_body}")
        raise

    print(f"Nudge sent to {nudge_to} — Resend id: {result.get('id')}")
