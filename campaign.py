"""Create and verify AC draft campaigns. Status 0 (draft) only — no send path.

Flow (proven working for this account):
  1. Legacy POST /admin/api.php?api_action=campaign_create
       — creates campaign with list + message attached in one call
  2. V3 PUT /api/3/campaigns/{id}
       — attaches segment (segmentid); v3 PUT works for this, legacy does not expose it
  3. V3 GET /api/3/campaigns/{id}
       — safety verification: status=0, send_amt=0, ldate=null
"""
import os
import requests as _requests
from ac_client import request as _v3

_DRAFT_STATUS = "0"
_AC_BASE = os.environ["AC_API_URL"].rstrip("/")
_AC_TOKEN = os.environ["AC_API_TOKEN"]


def _legacy(api_action: str, form_data: dict) -> dict:
    """
    POST to the AC legacy admin API. Prints the full raw response (never swallows it).
    Raises on result_code != 1.
    """
    url = f"{_AC_BASE}/admin/api.php"
    params = {"api_action": api_action, "api_output": "json", "api_key": _AC_TOKEN}
    resp = _requests.post(
        url,
        params=params,
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    print(f"[LEGACY {api_action}] HTTP {resp.status_code}")
    print(resp.text)
    body = resp.json()
    if body.get("result_code") != 1:
        raise RuntimeError(
            f"Legacy {api_action} failed — "
            f"result_code={body.get('result_code')}, "
            f"message={body.get('result_message')}"
        )
    return body


def verify_draft(campaign_id: str) -> dict:
    """GET campaign back and assert it is an unset draft. Raises loudly on violation."""
    _, body = _v3("GET", f"/api/3/campaigns/{campaign_id}")
    campaign = body["campaign"]

    status = str(campaign.get("status", ""))
    send_amt = str(campaign.get("send_amt", ""))
    ldate = campaign.get("ldate")

    errors = []
    if status != _DRAFT_STATUS:
        errors.append(f"status={status!r} (expected '0')")
    if send_amt != _DRAFT_STATUS:
        errors.append(f"send_amt={send_amt!r} (expected '0')")
    if ldate not in (None, "", "0000-00-00 00:00:00"):
        errors.append(f"ldate={ldate!r} (expected null)")

    if errors:
        raise RuntimeError(
            f"\n\n!!! SAFETY VIOLATION on campaign {campaign_id} !!!\n"
            + "\n".join(errors)
            + "\n\nManual review required immediately.\n"
        )

    return campaign


def _get_audience_count(list_id: str, segment_id: str) -> str:
    """Resolved contact count for list+segment via v3 contacts meta. Returns '?' on failure."""
    try:
        _, body = _v3(
            "GET",
            f"/api/3/contacts?listid={list_id}&segmentid={segment_id}&limit=1",
        )
        return str(body.get("meta", {}).get("total", "?"))
    except Exception:
        return "?"


def create_draft(
    message_id: str,
    segment_id: str,
    list_id: str,
    name: str,
) -> str:
    """
    Create an AC draft campaign (status=0), verify it, return campaign_id.
    There is no code path that sets a campaign to send.
    """
    # Step 1: create campaign with list + message via legacy API
    legacy_body = _legacy("campaign_create", {
        "type": "single",
        "name": name,
        "status": "0",
        "public": "1",
        f"p[{list_id}]": list_id,
        f"m[{message_id}]": "100",
    })
    campaign_id = str(legacy_body["id"])

    # Step 2: attach segment via v3 PUT (legacy has no segment field)
    _v3("PUT", f"/api/3/campaigns/{campaign_id}", json={"campaign": {
        "segmentid": int(segment_id),
        "bounceid": -1,
    }})

    # Step 3: safety gate — read back and assert draft state
    verify_draft(campaign_id)

    audience = _get_audience_count(list_id, segment_id)
    print(
        f"\nDRAFT VERIFIED -- campaign_id={campaign_id}, "
        f"segmentid={segment_id}, "
        f"audience_count={audience}\n"
    )
    return campaign_id
