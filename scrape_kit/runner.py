"""One job run: fetch -> parse -> write output."""

from __future__ import annotations

from typing import Any

import requests

from .fetch import FetchBlocked, fetch_html
from .output import write_rows
from .parse import parse_items


def run_job(cfg: dict[str, Any], session: requests.Session | None = None) -> dict[str, Any]:
    """Execute the configured job once. Returns a small summary dict.

    Raises FetchBlocked if robots.txt disallows the URL.
    """
    url = str(cfg["url"])
    html = fetch_html(url, cfg, session=session)
    rows = parse_items(html, cfg["parse"]["item_selector"], cfg["parse"]["fields"])
    destination = write_rows(rows, cfg["output"])
    return {"job": cfg.get("name", ""), "url": url, "rows": len(rows), "output": destination}
