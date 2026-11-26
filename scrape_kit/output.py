"""Output sinks: CSV, JSONL, and optional Google Sheets (via gspread).

Secrets handling: the Google Sheets path reads a service-account key file
whose location is given by the GOOGLE_SERVICE_ACCOUNT_JSON environment
variable. The key content is never logged, printed, or written to output.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

from .config import ConfigError


def _flatten(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return "; ".join(str(v) for v in value)
    return "" if value is None else str(value)


def write_rows(rows: list[dict[str, Any]], output_cfg: dict[str, Any]) -> str:
    """Write parsed rows to the configured sink. Returns the destination."""
    if not rows:
        return "(no rows)"
    out_type = output_cfg.get("type", "csv")
    if out_type == "csv":
        return _write_csv(rows, output_cfg)
    if out_type == "jsonl":
        return _write_jsonl(rows, output_cfg)
    if out_type == "sheets":
        return _write_sheets(rows, output_cfg)
    raise ConfigError(f"unknown output.type: {out_type!r}")


def _write_csv(rows: list[dict[str, Any]], output_cfg: dict[str, Any]) -> str:
    path = Path(output_cfg["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    append = bool(output_cfg.get("append", True)) and path.exists()
    fieldnames = list(rows[0].keys())
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not append:
            writer.writeheader()
        for row in rows:
            writer.writerow({k: _flatten(v) for k, v in row.items()})
    return str(path)


def _write_jsonl(rows: list[dict[str, Any]], output_cfg: dict[str, Any]) -> str:
    path = Path(output_cfg["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return str(path)


def _write_sheets(rows: list[dict[str, Any]], output_cfg: dict[str, Any]) -> str:
    try:
        import gspread
    except ImportError as e:
        raise ConfigError(
            "output.type=sheets needs gspread: pip install gspread "
            "and set GOOGLE_SERVICE_ACCOUNT_JSON to the service-account key file"
        ) from e
    key_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not key_file:
        raise ConfigError("set GOOGLE_SERVICE_ACCOUNT_JSON to the service-account key file path")
    client = gspread.service_account(filename=key_file)
    sheet = client.open(output_cfg["spreadsheet"])
    worksheet = sheet.sheet1
    header = list(rows[0].keys())
    existing = worksheet.row_values(1) if worksheet.row_count > 0 else []
    if existing[: len(header)] != header:
        worksheet.append_row(header)
    for row in rows:
        worksheet.append_row([_flatten(row.get(k, "")) for k in header])
    return f"google-sheets:{output_cfg['spreadsheet']}"
