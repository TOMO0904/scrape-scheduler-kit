"""Config validation tests."""

from __future__ import annotations

import pytest

from scrape_kit.config import ConfigError, load_config, validate_config

VALID = {
    "name": "x",
    "url": "https://example.com/",
    "parse": {"item_selector": "div.item", "fields": {"name": "h2::text"}},
    "output": {"type": "csv", "path": "out/x.csv"},
}


def test_valid_config_gets_defaults():
    cfg = validate_config(dict(VALID))
    assert cfg["respect_robots_txt"] is True
    assert cfg["schedule"]["every_minutes"] == 60
    assert cfg["output"]["append"] is True


def test_missing_keys_raise():
    with pytest.raises(ConfigError):
        validate_config({"name": "x"})
    bad = dict(VALID, url="ftp://nope")
    with pytest.raises(ConfigError):
        validate_config(bad)


def test_bad_field_spec_raises():
    bad = dict(VALID)
    bad["parse"] = {"item_selector": "div", "fields": {"x": "no-operator"}}
    with pytest.raises(ConfigError):
        validate_config(bad)


def test_sheets_requires_spreadsheet_name():
    bad = dict(VALID)
    bad["output"] = {"type": "sheets"}
    with pytest.raises(ConfigError):
        validate_config(bad)


def test_load_sample_job_file():
    from pathlib import Path
    sample = Path(__file__).resolve().parent.parent / "jobs" / "sample_quotes.yaml"
    cfg = load_config(sample)
    assert cfg["name"] == "quotes-sample"
    assert cfg["url"].startswith("https://")
