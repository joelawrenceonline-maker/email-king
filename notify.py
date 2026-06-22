"""Send the morning draft-reminder nudge to me only, via Resend API."""
import os
import json
import urllib.request

_SUBJECT = "Time to write today's email \U0001f4e7"
_RESEND_URL = "https://api.resend.com/emails"


def send_morning_nudge() -> None:
    """
    Send an HTML reminder to NUDGE_TO via Resend.
    This is the ONLY thing in this service that sends an email,
    and it sends only to a single personal address — never to a list.
    Raises on any Resend HTTP error (hard-fail).
    """
    api_key = os.environ["RESEND_API_KEY"]
    nudge_from = os.environ["NUDGE_FROM"]
    nudge_to = os.environ["NUDGE_TO"]
    draft_link = os.environ["DRAFT_LINK"]

    html_body = (
        "<!DOCTYPE html>"
        "<html><body style=\"font-family:Arial,sans-serif;padding:24px;color:#333;max-width:480px\">"
        "<p style=\"font-size:16px\">Open the <strong>Email King</strong> project and type <strong>&ldquo;go.&rdquo;</strong></p>"
        f"<p><a href=\"{draft_link}\""
        " style=\"display:inline-block;background:#5A67D8;color:#fff;padding:12px 28px;"
        "border-radius:6px;text-decoration:none;font-weight:bold;font-size:15px\">"
        "Open Email King &rarr;</a></p>"
        "</body></html>"
    )
    text_body = f'Open the Email King project and type "go."\n{draft_link}\n'

    payload = json.dumps({
        "from": nudge_from,
        "to": [nudge_to],
        "subject": _SUBJECT,
        "html": html_body,
        "text": text_body,
    }).encode()

    req = urllib.request.Request(
        _RESEND_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "email-king/0.4 (python-urllib)",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"[NUDGE HARD FAIL] HTTP {e.code}: {error_body}", flush=True)
        raise

    print(f"[nudge] Sent to {nudge_to} — Resend id: {result.get('id')}", flush=True)
