# scrape-scheduler-kit

[![CI](https://github.com/TOMO0904/scrape-scheduler-kit/actions/workflows/test.yml/badge.svg)](https://github.com/TOMO0904/scrape-scheduler-kit/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

A small Python kit for the classic freelance-job pattern **"fetch information
from a site on a schedule and write it to a spreadsheet/CSV"** (e.g. Etsy
orders → Google Sheets). Jobs are driven by one YAML config file, so the same
code is reused for every site.

- 日本語: [README.ja.md](README.ja.md)
- **Respects the target site**: `robots.txt` is checked before every fetch and
  disallowed URLs are refused. Also honor the site's Terms of Service — never
  point this at sites that prohibit automated access (Upwork, for example,
  bans scraping; use their official API/MCP instead).
- Polite by default: custom User-Agent, configurable delay between requests,
  timeout and retries.
- Local-first: results are written to local CSV/JSONL (or to a Google Sheet
  only if you explicitly configure it). No data is sent anywhere else.
- No secrets in code or logs: API keys / service-account files are read from
  environment variables only.

## Table of contents

- [Quick start](#quick-start)
- [Install](#install)
- [Job config (YAML)](#job-config-yaml)
- [Output types](#output-types)
- [Examples](#examples)
- [Tests and CI](#tests-and-ci)
- [Known limitations](#known-limitations)
- [Layout](#layout)
- [Security notes](#security-notes)
- [License](#license)
- [Changelog](#changelog)

## Quick start

```bash
pip install .                       # installs the `scrape-kit` command
scrape-kit validate examples/jobs/quotes_toscrape.yaml   # check the config
scrape-kit run examples/jobs/quotes_toscrape.yaml --once  # run once
scrape-kit run examples/jobs/quotes_toscrape.yaml         # loop on schedule (Ctrl+C to stop)
```

(`python -m scrape_kit ...` works too.) The sample job scrapes
<https://quotes.toscrape.com/> — a site built for scraping practice, with no
robots.txt restrictions — and appends to `out/quotes.csv`.

## Install

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt        # Windows
# .venv/bin/pip install -r requirements.txt          # macOS / Linux
# or directly: pip install .  (provides the `scrape-kit` command)
# optional, for Google Sheets output: pip install .[sheets]   (adds gspread)
# for development (tests): pip install .[dev]
```

Requires Python 3.10+.

## Job config (YAML)

```yaml
name: my-job                 # any label
url: https://example.org/list
respect_robots_txt: true     # keep true unless the site's terms allow automation
user_agent: "my-kit/0.1 (contact: you@example.com)"
timeout_seconds: 15
retries: 2
request_delay_seconds: 1.0   # polite delay between requests

parse:
  item_selector: "div.item"          # CSS selector for each row/item
  fields:
    title: "h2.title::text"          # one match  -> scalar
    price: "span.price::text"
    url:   "a.link::attr(href)"      # attribute extraction
    tags:  "span.tag::text"          # several matches -> list ("; "-joined in CSV)

output:
  type: csv                          # csv | jsonl | sheets
  path: "out/items.csv"              # for csv / jsonl
  append: true                       # scheduled runs append new rows
  # type: sheets                     # Google Sheets instead:
  # spreadsheet: "My Sheet Name"     # needs .[sheets] + GOOGLE_SERVICE_ACCOUNT_JSON

schedule:
  every_minutes: 60                  # loop mode interval
```

Field spec mini-language: `css::text`, `css::html`, `css::attr(name)`.

## Output types

| type | where | notes |
| --- | --- | --- |
| `csv` | local file (`output.path`) | header written once, then appended |
| `jsonl` | local file (`output.path`) | one JSON object per line |
| `sheets` | Google Sheets (`output.spreadsheet`) | needs `pip install .[sheets]` and the env var `GOOGLE_SERVICE_ACCOUNT_JSON` pointing at a service-account key file; the key is never logged |

## Examples

- [examples/jobs/quotes_toscrape.yaml](examples/jobs/quotes_toscrape.yaml) — sample job (CSV output, scraping-practice site)
- [examples/jobs/sheets_example.yaml](examples/jobs/sheets_example.yaml) — Google Sheets output variant (env-var key, dummy sheet name)

## Tests and CI

```bash
pip install .[dev]
python -m pytest -q
```

Covers the selector engine, config validation, the scheduler loop (short runs),
the robots.txt policy (mocked HTTP: disallow / per-user-agent / 404 / 5xx /
unreachable), Sheets output (mocked `gspread`, no real key), and full
fetch→parse→CSV runs against a local HTTP fixture — including a check that a
`robots.txt` `Disallow` blocks the fetch. No external network needed.
GitHub Actions runs the same suite on every push/PR across Python 3.10-3.13
(see the CI badge above).

## Known limitations

- Google Sheets output is tested with a mocked `gspread` only; it has **not**
  been verified against a real spreadsheet with a real service-account key.
- The scheduler loop is tested with short runs (`max_runs`), not with
  long-running operation.
- All network tests use a local HTTP fixture server; behavior against real
  sites (robots.txt variants, encodings, redirects) is not covered.
- robots.txt handling covers the common cases (401/403/404/410 → allow;
  5xx or unreachable → disallow all); not every RFC 9309 edge case is
  implemented.
- Static HTML only — no JavaScript rendering.

## Layout

```
scrape-scheduler-kit/
├── .github/workflows/test.yml      # CI (pytest on Python 3.10-3.13)
├── examples/                       # sample job YAMLs + examples README
│   └── jobs/
│       ├── quotes_toscrape.yaml    # CSV output sample
│       └── sheets_example.yaml     # Google Sheets sample (env-var key)
├── scrape_kit/
│   ├── config.py      # YAML job loading + validation
│   ├── fetch.py       # robots.txt policy, UA, timeout, retries, polite delay
│   ├── parse.py       # CSS-selector field extraction (bs4)
│   ├── output.py      # CSV / JSONL / Google Sheets sinks
│   ├── runner.py      # one job run: fetch -> parse -> output
│   ├── scheduler.py   # --once / interval loop
│   └── __main__.py    # CLI (scrape-kit)
├── jobs/sample_quotes.yaml
├── tests/             # unit + local end-to-end tests with fixtures
├── LICENSE  CHANGELOG.md  pyproject.toml
├── README.md  README.ja.md
└── requirements.txt / requirements-dev.txt
```

## Security notes

- Never target sites that prohibit automated access; `robots.txt` is enforced
  by default and overridable only explicitly per job.
- Secrets (service-account key files, API tokens) are read from environment
  variables only and are never written to code, logs, or output files.

## License

MIT — see [LICENSE](LICENSE).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
