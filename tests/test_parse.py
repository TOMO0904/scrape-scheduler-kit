"""Unit tests for the selector engine."""

from __future__ import annotations

import pytest

from scrape_kit.parse import extract, parse_items

HTML = """
<div class="item">
  <h2 class="name">Red Mug</h2>
  <span class="price">12.50</span>
  <a class="detail" href="/items/1">details</a>
  <span class="tag">kitchen</span><span class="tag">ceramic</span>
</div>
<div class="item">
  <h2 class="name">Blue Plate</h2>
  <span class="price">8.00</span>
  <a class="detail" href="/items/2">details</a>
  <span class="tag">kitchen</span>
</div>
"""

FIELDS = {
    "name": "h2.name::text",
    "price": "span.price::text",
    "link": "a.detail::attr(href)",
    "tags": "span.tag::text",
    "missing": "span.nope::text",
}


def test_parse_items_multiple_rows():
    rows = parse_items(HTML, "div.item", FIELDS)
    assert len(rows) == 2
    assert rows[0]["name"] == "Red Mug"
    assert rows[0]["price"] == "12.50"
    assert rows[0]["link"] == "/items/1"
    assert rows[1]["name"] == "Blue Plate"


def test_multi_match_returns_list():
    rows = parse_items(HTML, "div.item", FIELDS)
    assert rows[0]["tags"] == ["kitchen", "ceramic"]
    assert rows[1]["tags"] == "kitchen"  # single match -> scalar


def test_missing_selector_returns_empty_string():
    rows = parse_items(HTML, "div.item", FIELDS)
    assert rows[0]["missing"] == ""


def test_bad_spec_raises():
    from bs4 import BeautifulSoup
    with pytest.raises(ValueError):
        extract(BeautifulSoup(HTML, "html.parser"), "no-operator-here")
