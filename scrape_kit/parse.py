"""Config-driven HTML extraction.

Field specs are tiny strings:

- ``css::text``      -> text of the matched element(s)
- ``css::html``      -> inner HTML of the matched element(s)
- ``css::attr(name)`` -> the ``name`` attribute of the matched element(s)

One match  -> scalar value. Several matches -> list (joined with "; " on CSV
output). Zero matches -> "".
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

SPEC_RE = re.compile(r"^(?P<css>.+?)::(?P<op>text|html|attr\((?P<attr>[^)]+)\))$")


def extract(scope: Any, spec: str) -> Any:
    m = SPEC_RE.match(spec.strip())
    if not m:
        raise ValueError(f"bad field spec {spec!r}: expected 'css::text', 'css::html' or 'css::attr(name)'")
    nodes = scope.select(m.group("css"))
    op = m.group("op")
    if op == "text":
        values = [n.get_text(strip=True) for n in nodes]
    elif op == "html":
        values = [str(n) for n in nodes]
    else:
        values = [str(n.get(m.group("attr"), "")) for n in nodes]
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    return values


def parse_items(html: str, item_selector: str, fields: dict[str, str]) -> list[dict[str, Any]]:
    """Parse all items matching ``item_selector`` into a list of row dicts."""
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, Any]] = []
    for item in soup.select(item_selector):
        rows.append({name: extract(item, spec) for name, spec in fields.items()})
    return rows
