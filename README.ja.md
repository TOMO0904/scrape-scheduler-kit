# scrape-scheduler-kit

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

## インストール

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt        # Windows
# .venv/bin/pip install -r requirements.txt          # macOS / Linux
# 任意: Google Sheets出力に使う場合 pip install gspread
# 開発用（テスト含む）: pip install -r requirements-dev.txt
```

## クイックスタート

```bash
# 設定ファイルの検証
python -m scrape_kit validate jobs/sample_quotes.yaml

# 1回だけ実行
python -m scrape_kit run jobs/sample_quotes.yaml --once

# 設定したスケジュールで定期実行（Ctrl+Cで停止）
python -m scrape_kit run jobs/sample_quotes.yaml
```

サンプルジョブは <https://quotes.toscrape.com/>（スクレイピング練習用サイト・robots.txt制限なし）
を取得し、`out/quotes.csv` に追記します。

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
  # spreadsheet: "My Sheet Name"     # gspread と環境変数 GOOGLE_SERVICE_ACCOUNT_JSON が必要

schedule:
  every_minutes: 60                  # ループ実行の間隔（分）
```

フィールド指定のミニ言語: `css::text` / `css::html` / `css::attr(name)`。

## 出力タイプ

| type | 出力先 |備考 |
| --- | --- | --- |
| `csv` | ローカルファイル（`output.path`） | ヘッダは初回のみ、以後は追記 |
| `jsonl` | ローカルファイル（`output.path`） | 1行1 JSON |
| `sheets` | Google Sheets（`output.spreadsheet`） | `pip install gspread` と環境変数 `GOOGLE_SERVICE_ACCOUNT_JSON`（サービスアカウントキーのファイルパス）が必要。キー内容はログに出さない |

## テスト

```bash
python -m pytest -q
```

セレクタエンジン、設定バリデーション、ローカルHTTP fixtureに対する
取得→抽出→CSV出力の一気通貫テスト（robots.txtのDisallowで取得が拒否されることも含む）
をカバーします。外部ネットワーク不要です。

## 構成

```
scrape-scheduler-kit/
├── pyproject.toml
├── requirements.txt / requirements-dev.txt
├── scrape_kit/
│   ├── config.py      # YAMLジョブ設定の読み込み＋検証
│   ├── fetch.py       # robots.txtポリシー、UA、タイムアウト、リトライ、待機
│   ├── parse.py       # CSSセレクタによるフィールド抽出（bs4）
│   ├── output.py      # CSV / JSONL / Google Sheets の出力先
│   ├── runner.py      # 1回実行: fetch -> parse -> output
│   ├── scheduler.py   # --once /間隔ループ
│   └── __main__.py    # CLI
├── jobs/sample_quotes.yaml
└── tests/             # 単体テスト＋fixtureによるローカルend-to-endテスト
```

## ライセンス

MIT
