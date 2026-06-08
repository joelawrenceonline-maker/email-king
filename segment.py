"""Resolve a saved AC segment by exact name."""
from ac_client import request


def find_segment_by_name(name: str = "joe-favorite") -> str:
    """Return the segment id for the given exact name. Raises if not found."""
    _, body = request("GET", "/api/3/segments?limit=100")
    segments = body.get("segments", [])
    for seg in segments:
        if seg.get("name") == name:
            return str(seg["id"])
    names = [s.get("name") for s in segments]
    raise ValueError(
        f"Segment '{name}' not found. Available segments: {names}"
    )
