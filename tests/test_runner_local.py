"""End-to-end runner tests against a local HTTP fixture (no external network).

Serves tests/fixtures/site with http.server, then runs a full job:
fetch -> robots.txt check -> parse -> CSV output.
"""

from __future__ import annotations

import csv
import functools
import http.server
import threading
from pathlib import Path

import pytest

from scrape_kit.fetch import FetchBlocked
from scrape_kit.runner import run_job

SITE = Path(__file__).resolve().parent / "fixtures" / "site"


@pytest.fixture(scope="module")
def server_url():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    thread.join(timeout=5)


def _cfg(url: str, out_path: Path) -> dict:
    return {
        "name": "fixture-job",
        "url": url,
        "respect_robots_txt": True,
        "user_agent": "scrape-scheduler-kit-test/0.1",
        "timeout_seconds": 5,
        "retries": 0,
        "request_delay_seconds": 0,
        "parse": {
            "item_selector": "div.item",
            "fields": {
                "name": "h2.name::text",
                "price": "span.price::text",
                "link": "a.detail::attr(href)",
                "tags": "span.tag::text",
            },
        },
        "output": {"type": "csv", "path": str(out_path), "append": False},
        "schedule": {"every_minutes": 1},
    }


def test_run_job_writes_csv(server_url, tmp_path):
    out = tmp_path / "items.csv"
    result = run_job(_cfg(f"{server_url}/index.html", out))
    assert result["rows"] == 2
    assert out.is_file()
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert [r["name"] for r in rows] == ["Red Mug", "Blue Plate"]
    assert rows[0]["link"] == "/items/1"
    assert rows[0]["tags"] == "kitchen; ceramic"


def test_run_job_appends_on_second_run(server_url, tmp_path):
    out = tmp_path / "items.csv"
    cfg = _cfg(f"{server_url}/index.html", out)
    run_job(cfg)
    cfg["output"]["append"] = True
    run_job(cfg)
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert len(rows) == 4  # header written once, rows appended


def test_robots_txt_blocks_disallowed_path(server_url, tmp_path):
    out = tmp_path / "blocked.csv"
    cfg = _cfg(f"{server_url}/blocked.html", out)
    with pytest.raises(FetchBlocked):
        run_job(cfg)
    assert not out.exists()


def test_robots_can_be_disabled_explicitly(server_url, tmp_path):
    out = tmp_path / "blocked.csv"
    cfg = _cfg(f"{server_url}/blocked.html", out)
    cfg["respect_robots_txt"] = False
    cfg["parse"] = {"item_selector": "h1", "fields": {"title": "h1::text"}}
    result = run_job(cfg)
    assert result["rows"] == 1
