"""Resolve a saved AC segment by exact name."""
from ac_client import request


def find_segment_by_name(name: str = "joe-favorite") -> str:
    """Return the segment id for the given exact name. Raises if not found.
    Paginates through all segments in case the account has more than one page.
    """
    limit = 100
    offset = 0
    all_names = []

    while True:
        _, body = request("GET", f"/api/3/segments?limit={limit}&offset={offset}")
        segments = body.get("segments", [])

        for seg in segments:
            if seg.get("name") == name:
                return str(seg["id"])
            all_names.append(seg.get("name", ""))

        # Stop when we've received fewer results than the page size
        if len(segments) < limit:
            break
        offset += limit

    raise ValueError(
        f"Segment '{name}' not found after checking {len(all_names)} segments.\n"
        f"Available: {all_names}"
    )
