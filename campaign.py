"""Create and verify AC draft campaigns. Status 0 (draft) only — no send path."""
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
    """
    payload = {
        "campaign": {
            "type": "single",
            "status": 0,
            "name": name,
            "segmentid": int(segment_id),
            "lists": [{"list": {"id": list_id}}],
            "messages": [{"message": {"id": message_id}}],
        }
    }
    _, body = request("POST", "/api/3/campaigns", json=payload)
    campaign_id = str(body["campaign"]["id"])

    # Safety gate: immediately read back and assert draft state.
    verify_draft(campaign_id)

    audience = _get_audience_count(list_id, segment_id)
    print(
        f"\nDRAFT VERIFIED — campaign_id={campaign_id}, "
        f"list={list_id}, segment={segment_id}, "
        f"audience_count={audience}\n"
    )
    return campaign_id
