# Update Log

## v0.4.0 — 2026-06-22

Morning nudge cron — registered on Railway, fixed body/subject, GitHub auto-deploy wired up.

- `notify.py` — corrected subject to `"Time to write today's email 📧"`; switched body
  from plain-text to HTML with an "Open Email King →" button linking to `DRAFT_LINK`;
  kept hard-fail raise on Resend HTTP error; added `flush=True` to prints so Railway
  captures them before the cron container exits
- Railway cron service `morning-nudge` created in the `email-king` project, connected
  to `joelawrenceonline-maker/email-king`, start command `python main.py --nudge`,
  schedule `0 12 * * 1-5` (8 am ET Mon–Fri, EDT = UTC−4); switch to `0 13 * * 1-5`
  in November when clocks fall back to EST
- Required env vars set on the cron service: `RESEND_API_KEY`, `NUDGE_FROM`,
  `NUDGE_TO`, `DRAFT_LINK`
- GitHub auto-deploy enabled for both `email-king` and `morning-nudge` services —
  every push to `master` now deploys both automatically; no manual Railway deploys needed

## v0.3.0 — 2026-06-08

MCP server layer — exposes four tools over streamable HTTP on Railway.

- `mcp_server.py` — FastMCP server (`email-king`) with tools:
  - `find_segment(name)` — resolve a saved AC segment id by name
  - `create_message(subject, html)` — create AC message, verify HTML stored
  - `stage_draft(message_id, test)` — stage draft campaign for an existing message
  - `stage_email(subject, html, test)` — full pipeline: create message + stage draft
- `requirements.txt` — added `fastmcp>=2.0.0` and `uvicorn>=0.29.0`
- `Procfile` — changed from `worker: python main.py` to `web: python mcp_server.py`
- No send tool exists anywhere. All campaigns are created as drafts (status=0).
- MCP endpoint: `https://<railway-domain>/mcp`

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
