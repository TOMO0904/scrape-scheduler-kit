"""Unit tests for the robots.txt policy (no network: requests.get is mocked)."""

from __future__ import annotations

import requests

from scrape_kit.fetch import RobotsPolicy


class FakeResp:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


def _patch_robots(monkeypatch, handler) -> None:
    monkeypatch.setattr(
        "scrape_kit.fetch.requests.get",
        lambda url, headers=None, timeout=None: handler(url),
    )


def test_disallowed_path_is_blocked(monkeypatch):
    _patch_robots(monkeypatch, lambda url: FakeResp(200, "User-agent: *\nDisallow: /private\n"))
    policy = RobotsPolicy(respect=True, user_agent="test-bot/1.0")
    assert policy.allowed("https://example.com/private/page") is False
    assert policy.allowed("https://example.com/public") is True


def test_user_agent_specific_rule(monkeypatch):
    robots = "User-agent: badbot\nDisallow: /\n\nUser-agent: *\nAllow: /\n"
    _patch_robots(monkeypatch, lambda url: FakeResp(200, robots))
    assert RobotsPolicy(respect=True, user_agent="badbot/1.0").allowed("https://example.com/x") is False
    assert RobotsPolicy(respect=True, user_agent="goodbot/1.0").allowed("https://example.com/x") is True


def test_missing_robots_404_allows(monkeypatch):
    _patch_robots(monkeypatch, lambda url: FakeResp(404))
    assert RobotsPolicy(respect=True, user_agent="test-bot/1.0").allowed("https://example.com/") is True


def test_robots_401_403_410_allow(monkeypatch):
    for status in (401, 403, 410):
        _patch_robots(monkeypatch, lambda url, s=status: FakeResp(s))
        assert RobotsPolicy(respect=True, user_agent="test-bot/1.0").allowed("https://example.com/") is True


def test_server_error_disallows_all(monkeypatch):
    _patch_robots(monkeypatch, lambda url: FakeResp(500))
    assert RobotsPolicy(respect=True, user_agent="test-bot/1.0").allowed("https://example.com/") is False


def test_unreachable_robots_disallows_all(monkeypatch):
    def boom(url):
        raise requests.ConnectionError("unreachable")

    _patch_robots(monkeypatch, boom)
    assert RobotsPolicy(respect=True, user_agent="test-bot/1.0").allowed("https://example.com/") is False


def test_respect_false_never_fetches_robots(monkeypatch):
    def forbidden(url):
        raise AssertionError("robots.txt must not be fetched when respect=False")

    _patch_robots(monkeypatch, forbidden)
    policy = RobotsPolicy(respect=False, user_agent="test-bot/1.0")
    assert policy.allowed("https://example.com/blocked") is True
