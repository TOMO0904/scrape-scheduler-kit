# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-11-27

### Added

- `LICENSE` (MIT).
- CI: `.github/workflows/test.yml` runs the test suite on every push/PR across
  Python 3.10-3.13 (setup-python -> `pip install .[dev]` -> `pytest`).
- `examples/` with sample job YAMLs: `jobs/quotes_toscrape.yaml` (CSV output)
  and `jobs/sheets_example.yaml` (Google Sheets output via env-var key; no
  secrets in the repo), plus an examples README.
- `CHANGELOG.md` (this file).
- Tests:
  - scheduler loop short-run tests (`max_runs` + injectable `sleep_fn`), incl.
    error-continuation and sleep-interval checks;
  - Google Sheets output tests with a mocked `gspread` (no real key needed),
    plus the missing-`gspread` and missing-env-var error paths;
  - robots.txt policy unit tests with mocked HTTP: disallow rules, per-user-agent
    rules, 404 (allow), 5xx / unreachable (disallow all), `respect_robots_txt: false`.

### Changed

- `run_loop()` accepts optional keyword args `max_runs` and `sleep_fn` so the
  loop is testable/embeddable; default behavior (infinite loop) is unchanged.
- CLI program name shown in help is now `scrape-kit` (matches the console
  script installed by `pip install .`).
- `README.md` / `README.ja.md` strengthened at parity: badges (CI, license,
  Python version), table of contents, quick start via the `scrape-kit` command,
  examples, known limitations, links to `CHANGELOG.md`, updated layout tree.
- `pyproject.toml`: version 1.1.0, `setuptools>=77` build requirement (SPDX
  `license = "MIT"`), `authors`, `keywords`, `project.urls`.
- Default `user_agent` string bumped to `scrape-scheduler-kit/1.1`.

### Fixed

- Nothing. No behavior change to fetching, parsing, or output.

## [1.0.0] - 2026-11-27

- Initial public release: YAML-config-driven scraping + scheduled execution kit.
- robots.txt enforcement before every fetch (404/401/403/410 -> allow,
  5xx/unreachable -> disallow all), custom User-Agent, timeout, retries,
  polite request delay.
- CSS-selector field specs: `css::text`, `css::html`, `css::attr(name)`.
- Output sinks: local CSV, local JSONL, Google Sheets (optional `gspread` extra,
  key file path via `GOOGLE_SERVICE_ACCOUNT_JSON`; key content never logged).
- CLI: `scrape-kit run job.yaml [--once]` / `scrape-kit validate job.yaml`
  (also `python -m scrape_kit ...`).
- Tests: selector engine, config validation, full fetch->parse->CSV runs against
  a local HTTP fixture incl. a robots.txt `Disallow` block. No external network.
