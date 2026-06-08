# email-king

**IMPORTANT: This service never sends a marketing campaign.**
The only outbound email it generates is a personal nudge to one address.
Every campaign it creates has `status=0` (draft). There is no send-campaign code path.

---

## What it does

| Command | What happens |
|---------|-------------|
| `python main.py --nudge` | Sends *you* a reminder email: "Time to draft today's BCW email" |
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
| `DRAFT_LINK` | URL to open when the nudge arrives (e.g. your AC campaigns dashboard) |
| `SMTP_HOST` | SMTP server hostname for outbound nudge email |
| `SMTP_USER` | SMTP login username |
| `SMTP_PASS` | SMTP login password |
| `SMTP_FROM` | From address for nudge emails |

Copy `.env.example` → `.env` for local dev. `.env` is gitignored.

---

## Railway cron — morning nudge

Create a **Cron Job** service in Railway with:

- **Command:** `python main.py --nudge`
- **Schedule:** `0 13 * * 1-5`

This fires at **13:00 UTC**, which is:
- **8:00 AM EST** (UTC−5, Nov–Mar)
- **9:00 AM EDT** (UTC−4, Mar–Nov)

> Heads-up: Railway cron uses UTC. Adjust the hour by one in March and November
> when the US clocks change if exact 8 AM ET matters. A common compromise is
> `0 13 * * 1-5` year-round (8 AM EST / 9 AM EDT).

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

## Local dev

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in real values
set -a && source .env  # or: export $(cat .env | xargs)

python main.py --nudge
python main.py --draft --message-id 42 --test
```

On Windows PowerShell, load env vars with:
```powershell
Get-Content .env | ForEach-Object { if ($_ -match '^([^#][^=]*)=(.*)') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
```
