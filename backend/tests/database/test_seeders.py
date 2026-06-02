from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.database.seeders.runner import run_seeders
from app.database.seeders.stock_detail import StockDetailSeeder
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


def test_stock_detail_seeder_creates_tables_and_upserts_seed_rows(tmp_path: Path) -> None:
    seed_file = tmp_path / "stock_detail.csv"
    seed_file.write_text(
        "ticker,horizon,latest_price,daily_change,daily_change_percent,observed_at,"
        "forecast_status,forecast_generated_at,prediction_direction,"
        "prediction_confidence,prediction_expected_change_percent,"
        "prediction_risk_level,prediction_generated_at\n"
        "aapl, 1d ,214.35,2.62,1.24,2026-06-02T13:30:00Z,"
        " unavailable ,2026-06-02T13:15:00Z, bullish ,0.68,0.8,"
        " medium ,2026-06-02T13:18:00Z\n"
    )
    connection = RecordingConnection()

    StockDetailSeeder(seed_file=seed_file).run(connection)

    executions = connection.cursor_instance.executions
    assert "CREATE TABLE IF NOT EXISTS stock_market_details" in executions[0][0]
    assert "CREATE TABLE IF NOT EXISTS stock_forecast_details" in executions[1][0]
    assert "CREATE TABLE IF NOT EXISTS stock_prediction_details" in executions[2][0]

    market_upsert_params = [
        params for sql, params in executions if "INSERT INTO stock_market_details" in sql
    ]
    assert market_upsert_params == [
        {
            "ticker": "AAPL",
            "latest_price": 214.35,
            "daily_change": 2.62,
            "daily_change_percent": 1.24,
            "observed_at": "2026-06-02T13:30:00Z",
        }
    ]

    forecast_upsert_params = [
        params for sql, params in executions if "INSERT INTO stock_forecast_details" in sql
    ]
    assert forecast_upsert_params == [
        {
            "ticker": "AAPL",
            "horizon": "1d",
            "status": "unavailable",
            "generated_at": "2026-06-02T13:15:00Z",
        }
    ]

    prediction_upsert_params = [
        params for sql, params in executions if "INSERT INTO stock_prediction_details" in sql
    ]
    assert prediction_upsert_params == [
        {
            "ticker": "AAPL",
            "horizon": "1d",
            "direction": "bullish",
            "confidence": 0.68,
            "expected_change_percent": 0.8,
            "risk_level": "medium",
            "generated_at": "2026-06-02T13:18:00Z",
        }
    ]
    assert connection.commits == 1
