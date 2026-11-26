"""Google Sheets output tests with a mocked gspread (no real key, no network)."""

from __future__ import annotations

import sys
import types

import pytest

from scrape_kit.config import ConfigError
from scrape_kit.output import write_rows


class FakeWorksheet:
    def __init__(self) -> None:
        self.rows: list[list] = []

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def row_values(self, n: int) -> list:
        return self.rows[n - 1] if 0 < n <= len(self.rows) else []

    def append_row(self, row) -> None:
        self.rows.append(list(row))


class FakeSheet:
    def __init__(self) -> None:
        self.sheet1 = FakeWorksheet()


class FakeClient:
    def __init__(self) -> None:
        self.sheet = FakeSheet()
        self.opened: str | None = None
        self.key_file: str | None = None

    def open(self, name: str) -> FakeSheet:
        self.opened = name
        return self.sheet


def _install_fake_gspread(monkeypatch, client: FakeClient) -> None:
    module = types.ModuleType("gspread")

    def service_account(filename=None):
        client.key_file = filename
        return client

    module.service_account = service_account
    monkeypatch.setitem(sys.modules, "gspread", module)


def test_write_sheets_mocked_success(monkeypatch):
    client = FakeClient()
    _install_fake_gspread(monkeypatch, client)
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", "/dummy/service-account.json")

    rows = [{"a": "1", "b": ["x", "y"]}, {"a": "2", "b": "z"}]
    dest = write_rows(rows, {"type": "sheets", "spreadsheet": "My Sheet"})

    assert dest == "google-sheets:My Sheet"
    assert client.opened == "My Sheet"
    assert client.key_file == "/dummy/service-account.json"
    ws = client.sheet.sheet1
    assert ws.rows[0] == ["a", "b"]          # header written first
    assert ws.rows[1] == ["1", "x; y"]       # lists flattened with "; "
    assert ws.rows[2] == ["2", "z"]


def test_write_sheets_requires_env_var(monkeypatch):
    _install_fake_gspread(monkeypatch, FakeClient())
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    with pytest.raises(ConfigError, match="GOOGLE_SERVICE_ACCOUNT_JSON"):
        write_rows([{"a": "1"}], {"type": "sheets", "spreadsheet": "S"})


def test_write_sheets_requires_gspread(monkeypatch):
    # sys.modules entry of None makes `import gspread` raise ImportError.
    monkeypatch.setitem(sys.modules, "gspread", None)
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", "/dummy/service-account.json")
    with pytest.raises(ConfigError, match="gspread"):
        write_rows([{"a": "1"}], {"type": "sheets", "spreadsheet": "S"})
