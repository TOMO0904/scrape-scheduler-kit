# scrape-scheduler-kit

A small Python kit for the classic freelance-job pattern **"fetch information
from a site on a schedule and write it to a spreadsheet/CSV"** (e.g. Etsy
orders → Google Sheets). Jobs are driven by one YAML config file, so the same
code is reused for every site.

- Japanese README: [README.ja.md](README.ja.md)
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

## Install

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt        # Windows
# .venv/bin/pip install -r requirements.txt          # macOS / Linux
# optional, for Google Sheets output: pip install gspread
# for development (tests): pip install -r requirements-dev.txt
```

## Quick start

```bash
# validate a job config
python -m scrape_kit validate jobs/sample_quotes.yaml

# run once
python -m scrape_kit run jobs/sample_quotes.yaml --once

# run on the configured schedule (loop until Ctrl+C)
python -m scrape_kit run jobs/sample_quotes.yaml
```

The sample job scrapes <https://quotes.toscrape.com/> (a site built for
scraping practice, no robots.txt restrictions) and appends to
`out/quotes.csv`.

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
  # spreadsheet: "My Sheet Name"     # needs gspread + GOOGLE_SERVICE_ACCOUNT_JSON

schedule:
  every_minutes: 60                  # loop mode interval
```

Field spec mini-language: `css::text`, `css::html`, `css::attr(name)`.

## Output types

| type | where | notes |
| --- | --- | --- |
| `csv` | local file (`output.path`) | header written once, then appended |
| `jsonl` | local file (`output.path`) | one JSON object per line |
| `sheets` | Google Sheets (`output.spreadsheet`) | needs `pip install gspread` and the env var `GOOGLE_SERVICE_ACCOUNT_JSON` pointing at a service-account key file; the key is never logged |

## Tests

```bash
python -m pytest -q
```

Covers the selector engine, config validation, and full fetch→parse→CSV runs
against a local HTTP fixture — including a check that a `robots.txt`
`Disallow` blocks the fetch. No external network needed.

## Layout

```
scrape-scheduler-kit/
├── pyproject.toml
├── requirements.txt / requirements-dev.txt
├── scrape_kit/
│   ├── config.py      # YAML job loading + validation
│   ├── fetch.py       # robots.txt policy, UA, timeout, retries, polite delay
│   ├── parse.py       # CSS-selector field extraction (bs4)
│   ├── output.py      # CSV / JSONL / Google Sheets sinks
│   ├── runner.py      # one job run: fetch -> parse -> output
│   ├── scheduler.py   # --once / interval loop
│   └── __main__.py    # CLI
├── jobs/sample_quotes.yaml
└── tests/             # unit + local end-to-end tests with fixtures
```

## License

MIT
