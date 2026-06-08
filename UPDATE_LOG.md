# Update Log

## v0.2.0 — 2026-06-08

Switch nudge sender from SMTP to Resend HTTP API.

- `notify.py` — replaced smtplib with a direct POST to `https://api.resend.com/emails`
  using `RESEND_API_KEY` (Bearer) and `NUDGE_FROM` env vars; drops all `SMTP_*` vars
- `README.md` — env var table updated; SMTP vars removed
- `.env.example` — SMTP vars removed; RESEND_API_KEY and NUDGE_FROM added

## v0.1.0 — 2026-06-08

Initial build: weekday morning nudge + draft-only ActiveCampaign campaign stager
targeting the `joe-favorite` segment, replacing the old Zapier flow.

- `notify.py` — SMTP nudge to personal address only; never sends to a list
- `segment.py` — resolves segment by exact name, no hardcoded ids
- `message.py` — creates AC message with Arial 18pt wrapper
- `campaign.py` — creates draft (status=0) and asserts it with a safety verification
- `main.py` — CLI: `--nudge` and `--draft --message-id <ID> [--test]`
- Railway cron expression `0 13 * * 1-5` for 8 AM EST Mon–Fri
