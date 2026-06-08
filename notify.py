"""Send the morning draft-reminder nudge to me only, via SMTP."""
import os
import smtplib
from email.mime.text import MIMEText

_SUBJECT = "Time to draft today's BCW email"


def send_morning_nudge() -> None:
    """
    Send a plain-text reminder to NUDGE_TO.
    This is the ONLY thing in this service that sends an email,
    and it sends only to a single personal address — never to a list.
    """
    smtp_host = os.environ["SMTP_HOST"]
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]
    smtp_from = os.environ["SMTP_FROM"]
    nudge_to = os.environ["NUDGE_TO"]
    draft_link = os.environ["DRAFT_LINK"]

    body = f"Time to write today's BCW email. Open your draft here:\n{draft_link}\n"

    msg = MIMEText(body, "plain")
    msg["Subject"] = _SUBJECT
    msg["From"] = smtp_from
    msg["To"] = nudge_to

    with smtplib.SMTP_SSL(smtp_host, 465) as smtp:
        smtp.login(smtp_user, smtp_pass)
        smtp.sendmail(smtp_from, [nudge_to], msg.as_string())

    print(f"Nudge sent to {nudge_to}")
