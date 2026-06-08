"""
email-king MCP server — exposes campaign draft staging tools over streamable HTTP.

NO send tool. NO send path. Every campaign created here has status=0 (draft).
The human reviews and sends manually from the AC dashboard.

Tools:
  find_segment(name)               — resolve a saved AC segment id by name
  create_message(subject, html)    — create an AC message, verify html stored
  stage_draft(message_id, test)    — stage draft campaign for an existing message
  stage_email(subject, html, test) — full pipeline: create message + stage draft
"""
import json
import os
import uvicorn
from fastmcp import FastMCP
from fastmcp.server.http import create_streamable_http_app

mcp = FastMCP(
    "email-king",
    instructions=(
        "Email drafting tools for Business Credit Workshop. "
        "IMPORTANT: There is no send tool. All campaigns are created as drafts "
        "(status=0). After staging, open the campaign in ActiveCampaign, review it, "
        "and send manually. Never ask to send — that step is always manual."
    ),
)

_TEST_LIST = "7699"
_PROD_LIST = "22"


def _resolve_segment() -> str:
    return os.environ.get("SEGMENT_ID", "953")


def _list_id(test: bool) -> str:
    return _TEST_LIST if test else _PROD_LIST


@mcp.tool()
def find_segment(name: str = "joe-favorite") -> str:
    """
    Find a saved ActiveCampaign segment by exact name.
    Returns the numeric segment id as a string.
    """
    from segment import find_segment_by_name
    seg_id = find_segment_by_name(name)
    return f"Segment '{name}' found: id={seg_id}"


@mcp.tool()
def create_message(subject: str, html: str) -> str:
    """
    Create an ActiveCampaign message (email template) with the given subject
    and HTML body. Verifies the HTML is stored non-empty after creation.
    Returns the new message id.

    The caller is responsible for passing finished HTML. The subject must
    include any special characters (e.g. $) as literal text.
    """
    from message import create_message as _create
    message_id = _create(subject=subject, html=html)
    return f"Message created and verified: id={message_id}, subject={subject!r}"


@mcp.tool()
def stage_draft(message_id: str, test: bool = False) -> str:
    """
    Stage an ActiveCampaign draft campaign for an existing message id.

    Uses segment 953 (joe-favorite, ~16 475 contacts) from SEGMENT_ID env var.
    test=True  -> targets list 7699 (test audience, same segment filter)
    test=False -> targets list 22  (full production audience)

    Verifies status=0, send_amt=0, ldate=null before returning.
    There is no send path — the campaign is a draft only.
    Returns DRAFT VERIFIED with campaign_id and audience_count.
    """
    from campaign import create_draft, _get_audience_count, _resolve_address_id
    segment_id = _resolve_segment()
    list_id = _list_id(test)
    mode = "TEST" if test else "PRODUCTION"
    address_id = _resolve_address_id()
    campaign_id = create_draft(
        message_id=message_id,
        segment_id=segment_id,
        list_id=list_id,
        name=f"BCW Draft -- msg {message_id}",
    )
    audience = _get_audience_count(list_id, segment_id)
    return (
        f"DRAFT VERIFIED -- campaign_id={campaign_id}, "
        f"segmentid={segment_id}, addressid={address_id}, list={list_id} ({mode}), "
        f"audience_count={audience}"
    )


@mcp.tool()
def stage_email(subject: str, html: str, test: bool = False) -> str:
    """
    Full pipeline: create an AC message then stage it as a draft campaign.

    Steps (proven flow):
      1. POST /api/3/messages -- creates message, verifies html non-empty
      2. Legacy campaign_create -- creates draft with list + message attached
      3. V3 PUT segmentid=953 -- attaches joe-favorite segment
      4. V3 GET verification -- asserts status=0, send_amt=0, ldate=null

    test=True  -> list 7699 (test)
    test=False -> list 22  (production, ~16 475 contacts)

    There is NO send step here. Returns DRAFT VERIFIED once the campaign
    is sitting as a draft in ActiveCampaign.
    """
    from message import create_message as _create
    from campaign import create_draft, _get_audience_count, _resolve_address_id
    segment_id = _resolve_segment()
    list_id = _list_id(test)
    mode = "TEST" if test else "PRODUCTION"
    address_id = _resolve_address_id()

    message_id = _create(subject=subject, html=html)
    campaign_id = create_draft(
        message_id=message_id,
        segment_id=segment_id,
        list_id=list_id,
        name=f"BCW -- {subject}",
    )
    audience = _get_audience_count(list_id, segment_id)
    return (
        f"DRAFT VERIFIED -- message_id={message_id}, campaign_id={campaign_id}, "
        f"segmentid={segment_id}, addressid={address_id}, list={list_id} ({mode}), "
        f"audience_count={audience}"
    )


_HEALTH_BODY = json.dumps({"status": "ok", "service": "email-king"}).encode()
_HEALTH_HEADERS = [
    [b"content-type", b"application/json"],
    [b"content-length", str(len(_HEALTH_BODY)).encode()],
]


class _HealthMiddleware:
    """Intercept GET /health before the FastMCP app sees it."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http" and scope.get("path") in ("/health", "/healthz"):
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": _HEALTH_HEADERS,
            })
            await send({"type": "http.response.body", "body": _HEALTH_BODY})
        else:
            await self.app(scope, receive, send)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp_app = create_streamable_http_app(mcp, streamable_http_path="/mcp")
    app = _HealthMiddleware(mcp_app)
    uvicorn.run(app, host="0.0.0.0", port=port)
