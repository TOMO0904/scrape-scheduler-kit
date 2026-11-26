"""Simple interval scheduler for config-driven jobs.

``run_once`` executes a job a single time. ``run_loop`` repeats it every
``schedule.every_minutes`` minutes until interrupted (Ctrl+C). Errors are
logged to stderr and the loop continues; nothing is sent anywhere external
beyond the configured target URL.
"""

from __future__ import annotations

import sys
import time
from typing import Any

from .runner import run_job


def run_once(cfg: dict[str, Any]) -> dict[str, Any]:
    return run_job(cfg)


def run_loop(cfg: dict[str, Any]) -> None:
    every_minutes = float(cfg.get("schedule", {}).get("every_minutes", 60))
    print(f"[scrape-kit] job={cfg.get('name')} every {every_minutes} min. Ctrl+C to stop.", flush=True)
    while True:
        try:
            result = run_job(cfg)
            print(f"[scrape-kit] ok: {result}", flush=True)
        except Exception as e:  # keep the loop alive; message contains no secrets
            print(f"[scrape-kit] error: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        time.sleep(every_minutes * 60)
