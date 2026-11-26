"""Job configuration loading and validation (YAML driven)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

OUTPUT_TYPES = ("csv", "jsonl", "sheets")


class ConfigError(Exception):
    """Raised when a job config is missing or invalid."""


def load_config(path: str | Path) -> dict[str, Any]:
    """Load and validate one job YAML file. Returns a normalized config dict."""
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"config not found: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise ConfigError(f"invalid YAML in {path}: {e}") from e
    if not isinstance(raw, dict):
        raise ConfigError(f"config must be a mapping: {path}")
    cfg = dict(raw.get("job", raw))  # accept either top-level keys or a "job:" block
    return validate_config(cfg)


def validate_config(cfg: dict[str, Any]) -> dict[str, Any]:
    for key in ("name", "url", "parse", "output"):
        if key not in cfg:
            raise ConfigError(f"missing required key: {key!r}")
    if not str(cfg["url"]).startswith(("http://", "https://")):
        raise ConfigError(f"url must start with http:// or https://: {cfg['url']!r}")

    parse = cfg["parse"]
    if not isinstance(parse, dict) or not parse.get("item_selector") or not parse.get("fields"):
        raise ConfigError("parse.item_selector and parse.fields (non-empty mapping) are required")
    for field_name, spec in parse["fields"].items():
        if not isinstance(spec, str) or "::" not in spec:
            raise ConfigError(
                f"parse.fields.{field_name}: expected 'css::text', 'css::html' or 'css::attr(name)', got {spec!r}"
            )

    output = cfg["output"]
    if not isinstance(output, dict) or output.get("type", "csv") not in OUTPUT_TYPES:
        raise ConfigError(f"output.type must be one of {OUTPUT_TYPES}")
    if output.get("type") == "sheets" and not output.get("spreadsheet"):
        raise ConfigError("output.type=sheets requires output.spreadsheet (sheet name or URL)")
    if output.get("type") in ("csv", "jsonl") and not output.get("path"):
        raise ConfigError(f"output.type={output.get('type')} requires output.path")

    schedule = cfg.get("schedule", {})
    if "every_minutes" in schedule and float(schedule["every_minutes"]) <= 0:
        raise ConfigError("schedule.every_minutes must be > 0")

    cfg.setdefault("respect_robots_txt", True)
    cfg.setdefault("user_agent", "scrape-scheduler-kit/0.1")
    cfg.setdefault("timeout_seconds", 15)
    cfg.setdefault("retries", 2)
    cfg.setdefault("request_delay_seconds", 1.0)
    cfg.setdefault("schedule", {"every_minutes": 60})
    output.setdefault("type", "csv")
    output.setdefault("append", True)
    return cfg
