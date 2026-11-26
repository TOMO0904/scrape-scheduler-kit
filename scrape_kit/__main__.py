"""CLI: python -m scrape_kit <run|validate> <job.yaml> [--once]"""

from __future__ import annotations

import argparse
import sys

from .config import ConfigError, load_config
from .scheduler import run_loop, run_once


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scrape_kit", description="Config-driven scraping + scheduled run kit")
    parser.add_argument("command", choices=["run", "validate"], help="run the job, or only validate the config")
    parser.add_argument("config", help="path to a job YAML file")
    parser.add_argument("--once", action="store_true", help="run once instead of looping on schedule")
    args = parser.parse_args(argv)

    try:
        cfg = load_config(args.config)
    except ConfigError as e:
        print(f"[scrape-kit] config error: {e}", file=sys.stderr)
        return 2

    if args.command == "validate":
        print(f"[scrape-kit] config OK: {args.config} (job={cfg['name']}, url={cfg['url']})")
        return 0

    if args.once:
        try:
            print(run_once(cfg))
        except Exception as e:
            print(f"[scrape-kit] error: {type(e).__name__}: {e}", file=sys.stderr)
            return 1
        return 0

    try:
        run_loop(cfg)
    except KeyboardInterrupt:
        print("\n[scrape-kit] stopped.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
