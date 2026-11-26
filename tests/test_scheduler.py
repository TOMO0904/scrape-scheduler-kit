"""Short-run tests for the interval scheduler (no real sleeping, no network)."""

from __future__ import annotations

from scrape_kit.scheduler import run_loop, run_once


def test_run_loop_stops_after_max_runs(monkeypatch):
    calls = []

    def fake_run_job(cfg):
        calls.append(cfg)
        return {"job": cfg["name"], "rows": 1, "output": "x"}

    monkeypatch.setattr("scrape_kit.scheduler.run_job", fake_run_job)
    cfg = {"name": "t", "schedule": {"every_minutes": 0.001}}
    run_loop(cfg, max_runs=3, sleep_fn=lambda seconds: None)
    assert len(calls) == 3


def test_run_loop_continues_after_errors(monkeypatch, capsys):
    attempts = []

    def flaky(cfg):
        attempts.append(1)
        if len(attempts) < 3:
            raise RuntimeError("boom")
        return {"ok": True}

    monkeypatch.setattr("scrape_kit.scheduler.run_job", flaky)
    cfg = {"name": "t", "schedule": {"every_minutes": 0.001}}
    run_loop(cfg, max_runs=3, sleep_fn=lambda seconds: None)
    assert len(attempts) == 3
    assert "error" in capsys.readouterr().err


def test_run_loop_sleeps_configured_interval(monkeypatch):
    sleeps = []
    monkeypatch.setattr("scrape_kit.scheduler.run_job", lambda cfg: {"ok": 1})
    cfg = {"name": "t", "schedule": {"every_minutes": 2}}
    run_loop(cfg, max_runs=2, sleep_fn=sleeps.append)
    assert sleeps == [120.0]


def test_run_once_delegates(monkeypatch):
    monkeypatch.setattr("scrape_kit.scheduler.run_job", lambda cfg: {"done": True})
    assert run_once({"name": "x"}) == {"done": True}
