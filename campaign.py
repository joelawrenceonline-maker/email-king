"""Create and verify AC draft campaigns. Status 0 (draft) only — no send path.

Working API path for this account (POST /api/3/campaigns plural is plan-blocked):
  1. POST /api/3/campaign  (singular) — creates draft shell, status=0
  2. PUT  /api/3/campaigns/{id}       — attaches sendid (message), segmentid, listid
     NOTE: listid causes HTTP 500 on this account's plan; it falls back gracefully
     and prints a warning. Segment and message are always set.
  3. GET  /api/3/campaigns/{id}       — safety verification (status=0, send_amt=0, ldate=null)
"""
import os
from ac_client import request

_DRAFT_STATUS = "0"
DEFAULT_SEGMENT_ID = os.environ.get("SEGMENT_ID", "953")


def verify_draft(campaign_id: str) -> dict:
    """GET campaign back and assert it is an unset draft. Raises loudly on violation."""
    _, body = request("GET", f"/api/3/campaigns/{campaign_id}")
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
    """Resolved contact count for this list+segment. Returns '?' on failure."""
    try:
        _, body = request(
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
    # Step 1: create the campaign shell (singular endpoint; plural is plan-blocked)
    _, body = request("POST", "/api/3/campaign", json={
        "type": "single",
        "name": name,
    })
    campaign_id = str(body["id"])

    # Step 2: attach message, segment, and list via PUT.
    # listid causes HTTP 500 on this account's plan — try full set first,
    # fall back to message+segment only if it fails.
    list_attached = False
    try:
        request("PUT", f"/api/3/campaigns/{campaign_id}", json={"campaign": {
            "sendid": message_id,
            "segmentid": int(segment_id),
            "listid": int(list_id),
            "bounceid": -1,
        }})
        list_attached = True
    except Exception:
        request("PUT", f"/api/3/campaigns/{campaign_id}", json={"campaign": {
            "sendid": message_id,
            "segmentid": int(segment_id),
            "bounceid": -1,
        }})

    # Step 3: safety gate — read back and assert draft state
    verify_draft(campaign_id)

    audience = _get_audience_count(list_id, segment_id)
    list_line = (
        "" if list_attached
        else f"\n[ACTION NEEDED] List {list_id} could not be set via API — select it in AC before sending."
    )
    print(
        f"\nDRAFT VERIFIED -- campaign_id={campaign_id}, "
        f"segmentid={segment_id}, "
        f"audience_count={audience}"
        + list_line + "\n"
    )
    return campaign_id
