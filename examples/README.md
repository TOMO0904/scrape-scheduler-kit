# Examples

Job YAML files you can copy and adapt:

- `jobs/quotes_toscrape.yaml` — scrape <https://quotes.toscrape.com/> (a site
  built for scraping practice; no robots.txt restrictions) into a local CSV.
  Run: `scrape-kit run examples/jobs/quotes_toscrape.yaml --once`
- `jobs/sheets_example.yaml` — same scrape, but written to a Google Sheet.
  Requires `pip install .[sheets]` and the `GOOGLE_SERVICE_ACCOUNT_JSON`
  environment variable pointing at a service-account key file. The key file
  itself must never be committed or shared.

- 日本語: `jobs/quotes_toscrape.yaml` はローカルCSVへのサンプル、
  `jobs/sheets_example.yaml` はGoogle Sheets出力のサンプルです
  （`pip install .[sheets]` と環境変数 `GOOGLE_SERVICE_ACCOUNT_JSON` が必要。
  キーファイルは絶対にコミットしないこと）。

Never point these jobs at sites whose terms of service prohibit automated
access (Upwork, for example — use their official API/MCP instead).
スクレイピングを禁止しているサイト（例: Upwork）には絶対に向けないでください。
