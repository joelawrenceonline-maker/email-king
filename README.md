# email-king

**IMPORTANT: This service never sends a marketing campaign.**
The only outbound email it generates is a personal nudge to one address.
Every campaign it creates has `status=0` (draft). There is no send-campaign code path.

---

## What it does

| Command | What happens |
|---------|-------------|
| `python main.py --nudge` | Sends *you* a reminder email: "Time to write today's email 📧" |
| `python main.py --draft --message-id <ID>` | Creates an AC draft campaign targeting segment `joe-favorite` on list 22 |
| `python main.py --draft --message-id <ID> --test` | Same, but targets list 7699 (test audience) |

### Draft staging details
1. Resolves the AC segment named `joe-favorite` by exact name (never a hardcoded id).
2. Creates a campaign with `status=0`, `type=single`, attached to that segment and list.
3. Immediately GETs the campaign back and asserts `status=="0"`, `send_amt=="0"`, `ldate` is null.
4. Prints `DRAFT VERIFIED — campaign_id=…` on success. Raises loudly on any violation.
5. You then review and send manually inside the AC dashboard — **not here**.

---

## Environment variables

Set these in Railway (never commit real values):

| Variable | Description |
|----------|-------------|
| `AC_API_URL` | Your AC account API base URL, e.g. `https://youraccount.api-us1.com` |
| `AC_API_TOKEN` | ActiveCampaign API token (Settings → Developer) |
| `NUDGE_TO` | Your personal email address that receives the morning reminder |
| `NUDGE_FROM` | From address for nudge emails (must be a verified Resend sender) |
| `DRAFT_LINK` | URL to open when the nudge arrives (e.g. your AC campaigns dashboard) |
| `RESEND_API_KEY` | Resend API key for outbound nudge email |

Copy `.env.example` → `.env` for local dev. `.env` is gitignored.

---

## Railway cron — morning nudge

The **`morning-nudge`** cron service is live in the `email-king` Railway project.

- **Service:** `morning-nudge` (id: `bc83a1e7-1aaa-4030-b5be-4cb10de9f478`)
- **Command:** `python main.py --nudge`
- **Current schedule:** `0 12 * * 1-5` — fires **8:00 AM ET Mon–Fri (EDT = UTC−4)**
- **November DST:** change to `0 13 * * 1-5` when clocks fall back to EST (UTC−5)

Sends an HTML email with an "Open Email King →" button to `NUDGE_TO`.
Hard-fails (exits non-zero) if Resend returns an HTTP error — Railway will log it.

---

## Running a test draft (before touching the real audience)

```bash
# 1. Create (or locate) a message in AC and note its id, e.g. 42
# 2. Run in test mode — targets list 7699, not list 22
python main.py --draft --message-id 42 --test

# Expected output:
# Staging draft in TEST (list 7699) mode …
# Resolved segment 'joe-favorite' → id=<N>
# DRAFT VERIFIED — campaign_id=<ID>, list=7699, segment=<N>, audience_count=<N>
# Done. Campaign <ID> is sitting as a draft in ActiveCampaign.
```

Go into your AC dashboard, find the draft, and confirm it looks right.
Only after that should you run without `--test` (which targets list 22).

---

## MCP server

`mcp_server.py` runs as a FastMCP server over streamable HTTP. It is the primary
Railway process (`web:` in Procfile) and is how the Email King Claude project
calls into email-king.

### Tools exposed

| Tool | Args | What it does |
|------|------|-------------|
| `find_segment` | `name` | Resolve a saved AC segment id by exact name |
| `create_message` | `subject`, `html` | Create an AC message, verify HTML stored, return message id |
| `stage_draft` | `message_id`, `test?` | Stage a draft campaign for an existing message id |
| `stage_email` | `subject`, `html`, `test?` | Full pipeline: create message + stage draft in one call |

`test=true` targets list 7699 (test audience). `test=false` (default) targets list 22 (~16,475 contacts).
There is no send tool. All campaigns are created as drafts (status=0).

### MCP endpoint

```
https://<your-railway-domain>/mcp
```

Add this to Claude's MCP settings as a **Streamable HTTP** connection.

### Additional env vars needed

| Variable | Description |
|----------|-------------|
| `SEGMENT_ID` | Numeric segment id (default `953` for joe-favorite) |

---

## Local dev

```bash
pip install -r requirements.txt   # only requests; Resend uses stdlib urllib
cp .env.example .env   # fill in real values
set -a && source .env  # or: export $(cat .env | xargs)

python main.py --nudge
python main.py --draft --message-id 42 --test
```

On Windows PowerShell, load env vars with:
```powershell
Get-Content .env | ForEach-Object { if ($_ -match '^([^#][^=]*)=(.*)') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
```
