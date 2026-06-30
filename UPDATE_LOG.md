# Update Log

## v0.4.3 — 2026-06-30

Healthchecks.io monitoring — alert when morning nudge stops firing.

- `notify.py` — pings `HEALTHCHECK_URL` after every successful Resend delivery; non-fatal
  if the ping itself fails (logged but does not block the nudge)
- Railway `morning-nudge` — `HEALTHCHECK_URL` env var set to
  `https://hc-ping.com/142fac01-1fcd-42c7-820c-b0d2d4a316dd`
- Healthchecks check `morning-nudge` — schedule `0 12 * * 1-5` UTC, grace 2 hours,
  email alert to `joelawrenceonline@gmail.com` on "check goes down"
- If any weekday passes without a ping by 10:00 AM ET, an alert email fires automatically
- **November DST reminder:** update both Railway cron AND Healthchecks schedule from
  `0 12 * * 1-5` to `0 13 * * 1-5` when clocks fall back

## v0.4.2 — 2026-06-30

Fix morning-nudge never sending — GitHub auto-deploy had silently lost its connection to Railway,
so the v0.4.1 fix (removing `startCommand` from `railway.toml`) was never deployed. Every cron
run from June 24–30 was still using the June 22 image, which ran `mcp_server.py` (uvicorn)
instead of `main.py --nudge`. Confirmed via Resend dashboard: zero emails sent since June 8.

- Root cause: Railway GitHub App lost its branch tracking for both services; no webhooks
  were registered on the repo, and pushes after June 22 never triggered a deploy
- Fix: manually deployed fresh code to both services via Railway MCP; reconnected both
  services to `joelawrenceonline-maker/email-king@master` using `connect_service_source`,
  which immediately picked up the pending commits and restored auto-deploy
- `morning-nudge` start command changed from `python main.py --nudge` to
  `python -u main.py --nudge` — the `-u` flag forces unbuffered stdout so Railway captures
  logs even when the cron container exits in under a second
- Nudge confirmed working: email delivered to `joelawrenceonline@gmail.com` at 16:20 UTC
- If auto-deploy ever breaks again: run `connect_service_source` for both services via
  Railway MCP (no disconnect needed), or check `github.com/settings/installations` →
  Railway → confirm `email-king` repo is in the allowed list

## v0.4.1 — 2026-06-23

Fix morning-nudge cron never firing — railway.toml startCommand conflict.

- Root cause: `railway.toml` defined `startCommand = "python mcp_server.py"` at the
  project level, overriding the per-service UI setting on `morning-nudge` and causing
  it to run uvicorn (the MCP server) instead of `python main.py --nudge`; the cron
  schedule was also missing from the service config, so it ran as a regular always-on
  service rather than a cron job
- `railway.toml` — removed `startCommand`, `healthcheckPath`, and `healthcheckTimeout`
  from the shared `[deploy]` block; these are now set per-service in Railway directly
- Railway `morning-nudge` service — start command explicitly set to
  `python main.py --nudge`, cron schedule set to `0 12 * * 1-5` (8 AM ET Mon–Fri),
  health check cleared (not applicable to cron services)
- Railway `email-king` service — start command explicitly set to `python mcp_server.py`,
  health check path set to `/health`

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
