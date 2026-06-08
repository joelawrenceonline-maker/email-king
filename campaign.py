"""Create and verify AC draft campaigns. Status 0 (draft) only — no send path.

API note: POST /api/3/campaigns (plural) is blocked at the account plan level for
this account. The working path is:
  1. POST /api/3/campaign (singular)  — creates draft, returns id
  2. PUT  /api/3/campaigns/{id}       — sets sendid (message) and segmentid
  3. GET  /api/3/campaigns/{id}       — safety verification

List attachment (POST /api/3/campaignLists) is also blocked. The draft will be
created without a list selected. Before sending, open the campaign in the AC UI
and choose the list — that is the ONLY manual step required.
"""
from ac_client import request

_DRAFT_STATUS = "0"


def verify_draft(campaign_id: str) -> dict:
    """
    GET the campaign back and assert it is an unset draft.
    Raises loudly on any violation. Returns the campaign dict.
    """
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
    """Best-effort contact count for this list+segment. Returns '?' on failure."""
    try:
        _, body = request(
            "GET",
            f"/api/3/contacts?listid={list_id}&segmentid={segment_id}&limit=1",
        )
        total = body.get("meta", {}).get("total", "?")
        return str(total)
    except Exception:
        return "?"


def create_draft(
    message_id: str,
    segment_id: str,
    list_id: str,
    name: str,
) -> str:
    """
    Create an AC campaign with status=0 (draft only), verify it, and return the
    campaign id. There is no code path that sets a campaign to send.

    Three-step process (POST /campaigns plural is blocked at account level):
      1. POST /api/3/campaign (singular) — create the campaign shell
      2. PUT  /api/3/campaigns/{id}      — attach message (sendid) and segment
      3. GET  /api/3/campaigns/{id}      — safety verification

    NOTE: list attachment via API is also blocked. The draft will appear in AC
    without a list selected. Open it in the AC dashboard and add the list before
    sending — that is the only manual step required.
    """
    # Step 1: create the campaign shell (singular endpoint is the only one that works)
    _, body = request("POST", "/api/3/campaign", json={
        "type": "single",
        "name": name,
    })
    campaign_id = str(body["id"])

    # Step 2: attach message and segment via PUT
    request("PUT", f"/api/3/campaigns/{campaign_id}", json={"campaign": {
        "sendid": message_id,
        "segmentid": int(segment_id),
        "bounceid": -1,
    }})

    # Safety gate: immediately read back and assert draft state.
    verify_draft(campaign_id)

    audience = _get_audience_count(list_id, segment_id)
    print(
        f"\nDRAFT VERIFIED -- campaign_id={campaign_id}, "
        f"segment={segment_id}, message={message_id}, "
        f"audience_count={audience}\n"
        f"ACTION NEEDED: open campaign {campaign_id} in AC and select list {list_id} before sending.\n"
    )
    return campaign_id
