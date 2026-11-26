"""Polite fetching: robots.txt enforcement, user agent, timeout, retries, delay.

The kit refuses to fetch URLs that the target site's robots.txt disallows
(disable only with ``respect_robots_txt: false`` and only for sites whose
terms of service allow it). Never point this at sites that prohibit
automated access.
"""

from __future__ import annotations

import time
import urllib.robotparser
from typing import Any
from urllib.parse import urljoin, urlparse

import requests


class FetchBlocked(Exception):
    """robots.txt disallows this URL."""


class FetchError(Exception):
    """The page could not be fetched after retries."""


class RobotsPolicy:
    """Caches one robots.txt per host and answers can_fetch() for URLs."""

    def __init__(self, respect: bool, user_agent: str, timeout: float = 10.0) -> None:
        self.respect = respect
        self.user_agent = user_agent
        self.timeout = timeout
        self._parsers: dict[str, urllib.robotparser.RobotFileParser] = {}

    def allowed(self, url: str) -> bool:
        if not self.respect:
            return True
        robots_url = urljoin(url, "/robots.txt")
        if robots_url not in self._parsers:
            self._parsers[robots_url] = self._fetch_robots(robots_url)
        return self._parsers[robots_url].can_fetch(self.user_agent, url)

    def _fetch_robots(self, robots_url: str) -> urllib.robotparser.RobotFileParser:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        try:
            resp = requests.get(robots_url, headers={"User-Agent": self.user_agent}, timeout=self.timeout)
        except requests.RequestException:
            # robots.txt unreachable: be conservative and disallow.
            rp.parse(["User-agent: *", "Disallow: /"])
            return rp
        if resp.status_code == 200:
            rp.parse(resp.text.splitlines())
        elif resp.status_code in (401, 403, 404, 410):
            rp.parse([])  # no robots.txt -> allowed
        else:
            # 5xx etc.: per RFC 9309 treat as "disallow all".
            rp.parse(["User-agent: *", "Disallow: /"])
        return rp


class PoliteTimer:
    """Keeps at least `delay` seconds between requests to the same host."""

    def __init__(self, delay: float) -> None:
        self.delay = max(0.0, float(delay))
        self._last: dict[str, float] = {}

    def wait(self, url: str) -> None:
        host = urlparse(url).netloc
        now = time.monotonic()
        last = self._last.get(host)
        if last is not None and self.delay > 0:
            remaining = self.delay - (now - last)
            if remaining > 0:
                time.sleep(remaining)
        self._last[host] = time.monotonic()


def fetch_html(url: str, cfg: dict[str, Any], session: requests.Session | None = None) -> str:
    """Fetch one page, honoring robots.txt, polite delay, timeout and retries."""
    session = session or requests.Session()
    policy = RobotsPolicy(bool(cfg.get("respect_robots_txt", True)), str(cfg.get("user_agent", "scrape-scheduler-kit")))
    if not policy.allowed(url):
        raise FetchBlocked(f"robots.txt disallows fetching: {url}")

    PoliteTimer(cfg.get("request_delay_seconds", 1.0)).wait(url)
    headers = {"User-Agent": str(cfg.get("user_agent", "scrape-scheduler-kit"))}
    timeout = float(cfg.get("timeout_seconds", 15))
    retries = int(cfg.get("retries", 2))

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = session.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or resp.encoding
            return resp.text
        except requests.RequestException as e:
            last_error = e
            if attempt < retries:
                time.sleep(0.5 * (2 ** attempt))
    raise FetchError(f"failed to fetch {url} after {retries + 1} attempts: {last_error}")
