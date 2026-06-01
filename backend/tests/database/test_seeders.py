from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.database.seeders.runner import run_seeders
from app.database.seeders.supported_stocks import SupportedStocksSeeder


@dataclass
class RecordingSeeder:
    name: str
    calls: list[str]

    def run(self, connection: object) -> None:
        self.calls.append(f"{self.name}:{id(connection)}")


def test_run_seeders_runs_each_seeder_in_order_with_same_connection() -> None:
    calls: list[str] = []
    connection = object()

    run_seeders(
        connection,
        [
            RecordingSeeder(name="first", calls=calls),
            RecordingSeeder(name="second", calls=calls),
        ],
    )

    assert calls == [f"first:{id(connection)}", f"second:{id(connection)}"]


class RecordingCursor:
    def __init__(self) -> None:
        self.executions: list[tuple[str, object]] = []

    def execute(self, sql: str, params: object = None) -> None:
        self.executions.append((sql, params))

    def __enter__(self) -> "RecordingCursor":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class RecordingConnection:
    def __init__(self) -> None:
        self.cursor_instance = RecordingCursor()
        self.commits = 0

    def cursor(self) -> RecordingCursor:
        return self.cursor_instance

    def commit(self) -> None:
        self.commits += 1


def test_supported_stocks_seeder_creates_table_and_upserts_seed_rows(tmp_path: Path) -> None:
    seed_file = tmp_path / "supported_stocks.csv"
    seed_file.write_text(
        "ticker,company_name,exchange,instrument_type,region,is_supported\n"
        "AAPL,Apple Inc.,NASDAQ,common_stock,US,true\n"
        "SPY,SPDR S&P 500 ETF,NYSE Arca,etf,US,false\n"
    )
    connection = RecordingConnection()

    SupportedStocksSeeder(seed_file=seed_file).run(connection)

    executions = connection.cursor_instance.executions
    assert "CREATE TABLE IF NOT EXISTS supported_stocks" in executions[0][0]
    upsert_params = [params for sql, params in executions if "INSERT INTO supported_stocks" in sql]
    assert upsert_params == [
        {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "exchange": "NASDAQ",
            "instrument_type": "common_stock",
            "region": "US",
            "is_supported": True,
            "search_text": "aapl apple inc. nasdaq",
        }
    ]
    assert connection.commits == 1
