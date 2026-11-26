# scrape-scheduler-kit

[![CI](https://github.com/TOMO0904/scrape-scheduler-kit/actions/workflows/test.yml/badge.svg)](https://github.com/TOMO0904/scrape-scheduler-kit/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

「指定サイトの情報を定期的に取得してスプレッドシート/CSVへ出力する」
という定番案件（例: Etsyの受注をGoogle Sheetsへ自動反映）を、
1つのYAML設定ファイルで使い回せる小型Pythonキットです。

- English README: [README.md](README.md)
- **対象サイトの規約を尊重**: 取得前に必ず `robots.txt` を確認し、
  DisallowされたURLは取得を拒否します。robots.txtだけでなく利用規約も確認し、
  自動アクセスを禁止しているサイト（例: Upwork — スクレイピングは規約違反のため
  公式API/MCPを使うこと）には絶対に向けないでください。
- 丁寧なアクセス: カスタムUser-Agent、リクエスト間隔、タイムアウト、リトライつき。
- ローカル完結: 出力はローカルのCSV/JSONL（Google Sheetsは明示的に設定した場合のみ）。
  それ以外への外部送信はしません。
- 秘密情報はコード・ログに出さない: APIキーやサービスアカウントファイルは
  環境変数からのみ読みます。

## 目次

- [クイックスタート](#クイックスタート)
- [インストール](#インストール)
- [ジョブ設定（YAML）](#ジョブ設定yaml)
- [出力タイプ](#出力タイプ)
- [サンプル](#サンプル)
- [テストとCI](#テストとci)
- [既知の制限](#既知の制限)
- [構成](#構成)
- [セキュリティ](#セキュリティ)
- [ライセンス](#ライセンス)
- [変更履歴](#変更履歴)

## クイックスタート

```bash
pip install .                       # `scrape-kit` コマンドが入る
scrape-kit validate examples/jobs/quotes_toscrape.yaml   # 設定の検証
scrape-kit run examples/jobs/quotes_toscrape.yaml --once  # 1回だけ実行
scrape-kit run examples/jobs/quotes_toscrape.yaml         # スケジュール実行（Ctrl+Cで停止）
```

（`python -m scrape_kit ...` でも動きます。）サンプルジョブは
スクレイピング練習用サイト <https://quotes.toscrape.com/>（robots.txt制限なし）
を取得し、`out/quotes.csv` に追記します。

## インストール

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt        # Windows
# .venv/bin/pip install -r requirements.txt          # macOS / Linux
# または直接: pip install .（`scrape-kit` コマンドが入る）
# 任意: Google Sheets出力に使う場合 pip install .[sheets]（gspread追加）
# 開発用（テスト含む）: pip install .[dev]
```

Python 3.10以上が必要です。

## ジョブ設定（YAML）

```yaml
name: my-job                 # 任意のラベル
url: https://example.org/list
respect_robots_txt: true     # サイトの規約で自動化が許される場合以外は true のまま
user_agent: "my-kit/0.1 (contact: you@example.com)"
timeout_seconds: 15
retries: 2
request_delay_seconds: 1.0   # リクエスト間の待機（丁寧さ）

parse:
  item_selector: "div.item"          # 各行・各アイテムのCSSセレクタ
  fields:
    title: "h2.title::text"          # 1件ヒット -> そのままの値
    price: "span.price::text"
    url:   "a.link::attr(href)"      # 属性の抽出
    tags:  "span.tag::text"          # 複数ヒット -> リスト（CSVでは "; " 区切り）

output:
  type: csv                          # csv | jsonl | sheets
  path: "out/items.csv"              # csv / jsonl の場合
  append: true                       # 定期実行時は追記
  # type: sheets                     # Google Sheetsに出す場合:
  # spreadsheet: "My Sheet Name"     # .[sheets] と環境変数 GOOGLE_SERVICE_ACCOUNT_JSON が必要

schedule:
  every_minutes: 60                  # ループ実行の間隔（分）
```

フィールド指定のミニ言語: `css::text` / `css::html` / `css::attr(name)`。

## 出力タイプ

| type | 出力先 |備考 |
| --- | --- | --- |
| `csv` | ローカルファイル（`output.path`） | ヘッダは初回のみ、以後は追記 |
| `jsonl` | ローカルファイル（`output.path`） | 1行1 JSON |
| `sheets` | Google Sheets（`output.spreadsheet`） | `pip install .[sheets]` と環境変数 `GOOGLE_SERVICE_ACCOUNT_JSON`（サービスアカウントキーのファイルパス）が必要。キー内容はログに出さない |

## サンプル

- [examples/jobs/quotes_toscrape.yaml](examples/jobs/quotes_toscrape.yaml) — CSV出力のサンプルジョブ（練習用サイト）
- [examples/jobs/sheets_example.yaml](examples/jobs/sheets_example.yaml) — Google Sheets出力の例（環境変数キー・ダミーのシート名）

## テストとCI

```bash
pip install .[dev]
python -m pytest -q
```

セレクタエンジン、設定バリデーション、スケジューラループ（短時間実行）、
robots.txtポリシー（モックHTTP: Disallow/ユーザーエージェント別/404/5xx/到達不能）、
Sheets出力（gspreadをモック・実キー不要）、ローカルHTTP fixtureに対する
取得→抽出→CSV出力の一気通貫テスト（robots.txtのDisallowで取得が拒否されることも含む）
をカバーします。外部ネットワーク不要です。
GitHub Actionsが push/PR ごとに Python 3.10〜3.13 で同じテストを実行します（上部のCIバッジ参照）。

## 既知の制限

- Google Sheets出力はモックした `gspread` でのみテスト済み。実際のスプレッドシート・
  実キーでの検証は**未実施**です。
- スケジューラループは短時間実行（`max_runs`）でのみテスト済み。長時間運転は未検証です。
- ネットワークテストはすべてローカルのHTTP fixtureサーバーに対するものです。
  実サイト（robots.txtの細かい変種、文字コード、リダイレクト）への behavior は未カバーです。
- robots.txt の扱いは一般的なケース（401/403/404/410 → 許可、5xx・到達不能 → 全拒否）をカバー。
  RFC 9309 の細部までは網羅していません。
- 静的HTMLのみ対象。JavaScriptレンダリングには対応していません。

## 構成

```
scrape-scheduler-kit/
├── .github/workflows/test.yml      # CI（Python 3.10〜3.13でpytest）
├── examples/                       # サンプルジョブYAML + examples README
│   └── jobs/
│       ├── quotes_toscrape.yaml    # CSV出力のサンプル
│       └── sheets_example.yaml     # Google Sheetsのサンプル（環境変数キー）
├── scrape_kit/
│   ├── config.py      # YAMLジョブ設定の読み込み＋検証
│   ├── fetch.py       # robots.txtポリシー、UA、タイムアウト、リトライ、待機
│   ├── parse.py       # CSSセレクタによるフィールド抽出（bs4）
│   ├── output.py      # CSV / JSONL / Google Sheets の出力先
│   ├── runner.py      # 1回実行: fetch -> parse -> output
│   ├── scheduler.py   # --once /間隔ループ
│   └── __main__.py    # CLI（scrape-kit）
├── jobs/sample_quotes.yaml
├── tests/             # 単体テスト＋fixtureによるローカルend-to-endテスト
├── LICENSE  CHANGELOG.md  pyproject.toml
├── README.md  README.ja.md
└── requirements.txt / requirements-dev.txt
```

## セキュリティ

- 自動アクセスを禁止しているサイトには絶対に向けないこと。`robots.txt` は既定で強制され、
 ジョブごとに明示した場合のみ解除できます。
- 秘密情報（サービスアカウントキー、APIトークン）は環境変数からのみ読み、
  コード・ログ・出力ファイルには一切書きません。

## ライセンス

MIT — [LICENSE](LICENSE) を参照。

## 変更履歴

[CHANGELOG.md](CHANGELOG.md) を参照。
