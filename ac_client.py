"""Thin ActiveCampaign API v3 wrapper."""
import os
import requests

AC_API_URL = os.environ["AC_API_URL"].rstrip("/")
AC_API_TOKEN = os.environ["AC_API_TOKEN"]

_SESSION = requests.Session()
_SESSION.headers.update({"Api-Token": AC_API_TOKEN, "Content-Type": "application/json"})


def request(method: str, path: str, **kwargs):
    """Return (status_code, json_body). Prints full body on any non-2xx."""
    url = f"{AC_API_URL}{path}"
    resp = _SESSION.request(method, url, **kwargs)
    try:
        body = resp.json()
    except Exception:
        body = resp.text
    if not resp.ok:
        print(f"[AC ERROR] {method} {path} -> {resp.status_code}")
        print(body)
        resp.raise_for_status()
    return resp.status_code, body
