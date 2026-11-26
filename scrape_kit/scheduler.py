"""Simple interval scheduler for config-driven jobs.

``run_once`` executes a job a single time. ``run_loop`` repeats it every
``schedule.every_minutes`` minutes until interrupted (Ctrl+C). Errors are
logged to stderr and the loop continues; nothing is sent anywhere external
beyond the configured target URL.

``run_loop`` also accepts ``max_runs`` and ``sleep_fn`` so the loop can be
tested or embedded; with the defaults its behavior is an infinite loop.
"""

from __future__ import annotations

import sys
import time
from typing import Any, Callable

from .runner import run_job


def run_once(cfg: dict[str, Any]) -> dict[str, Any]:
    return run_job(cfg)


def run_loop(
    cfg: dict[str, Any],
    *,
    max_runs: int | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> None:
    every_minutes = float(cfg.get("schedule", {}).get("every_minutes", 60))
    print(f"[scrape-kit] job={cfg.get('name')} every {every_minutes} min. Ctrl+C to stop.", flush=True)
    runs = 0
    while True:
        try:
            result = run_job(cfg)
            print(f"[scrape-kit] ok: {result}", flush=True)
        except Exception as e:  # keep the loop alive; message contains no secrets
            print(f"[scrape-kit] error: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        runs += 1
        if max_runs is not None and runs >= max_runs:
            return
        sleep_fn(every_minutes * 60)
