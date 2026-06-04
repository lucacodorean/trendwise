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
        self.fetchone_results: list[tuple[int, ...] | None] = [(42,), (100,), (200,)]

    def execute(self, sql: str, params: object = None) -> None:
        self.executions.append((sql, params))

    def fetchone(self) -> tuple[int, ...] | None:
        return self.fetchone_results.pop(0)

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


def test_supported_stocks_seeder_upserts_seed_rows_into_migrated_stocks_table(
    tmp_path: Path,
) -> None:
    seed_file = tmp_path / "supported_stocks.csv"
    seed_file.write_text(
        "ticker,company_name,exchange,instrument_type,region,is_supported\n"
        "AAPL,Apple Inc.,NASDAQ,common_stock,US,true\n"
        "SPY,SPDR S&P 500 ETF,NYSE Arca,etf,US,false\n"
    )
    connection = RecordingConnection()

    SupportedStocksSeeder(seed_file=seed_file).run(connection)

    executions = connection.cursor_instance.executions
    assert all("CREATE TABLE" not in sql for sql, _ in executions)
    assert any("INSERT INTO stocks" in sql for sql, _ in executions)
    upsert_params = [params for sql, params in executions if "INSERT INTO stocks" in sql]
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


def test_stock_detail_seeder_inserts_seed_rows_into_migrated_tables(
    tmp_path: Path,
) -> None:
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
    assert all("CREATE TABLE" not in sql for sql, _ in executions)
    assert any("INSERT INTO market_snapshots" in sql for sql, _ in executions)
    assert any("INSERT INTO forecast_runs" in sql for sql, _ in executions)
    assert any("INSERT INTO prediction_runs" in sql for sql, _ in executions)

    market_insert_params = [
        params for sql, params in executions if "INSERT INTO market_snapshots" in sql
    ]
    market_insert_sql = [
        sql for sql, _ in executions if "INSERT INTO market_snapshots" in sql
    ][0]
    assert "ON CONFLICT (stock_id, provider, observed_at) DO UPDATE SET" in market_insert_sql
    assert "latest_price = EXCLUDED.latest_price" in market_insert_sql
    assert "daily_change = EXCLUDED.daily_change" in market_insert_sql
    assert "daily_change_percent = EXCLUDED.daily_change_percent" in market_insert_sql
    assert market_insert_params == [
        {
            "stock_id": 42,
            "provider": "seed",
            "latest_price": 214.35,
            "daily_change": 2.62,
            "daily_change_percent": 1.24,
            "observed_at": "2026-06-02T13:30:00Z",
        }
    ]

    forecast_insert_params = [
        params for sql, params in executions if "INSERT INTO forecast_runs" in sql
    ]
    forecast_insert_sql = [sql for sql, _ in executions if "INSERT INTO forecast_runs" in sql][0]
    assert "ON CONFLICT (stock_id, horizon, generated_at) DO UPDATE SET" in forecast_insert_sql
    assert "status = EXCLUDED.status" in forecast_insert_sql
    assert forecast_insert_params == [
        {
            "stock_id": 42,
            "horizon": "1d",
            "status": "unavailable",
            "generated_at": "2026-06-02T13:15:00Z",
        }
    ]

    forecast_source_insert_params = [
        params
        for sql, params in executions
        if "INSERT INTO forecast_source_market_snapshots" in sql
    ]
    forecast_source_insert_sql = [
        sql
        for sql, _ in executions
        if "INSERT INTO forecast_source_market_snapshots" in sql
    ][0]
    assert "ON CONFLICT (forecast_run_id, market_snapshot_id) DO NOTHING" in forecast_source_insert_sql
    assert forecast_source_insert_params == [
        {
            "forecast_run_id": 200,
            "market_snapshot_id": 100,
        }
    ]

    prediction_insert_params = [
        params for sql, params in executions if "INSERT INTO prediction_runs" in sql
    ]
    prediction_insert_sql = [sql for sql, _ in executions if "INSERT INTO prediction_runs" in sql][0]
    assert (
        "ON CONFLICT (stock_id, horizon, forecast_run_id, generated_at) DO UPDATE SET"
        in prediction_insert_sql
    )
    assert "direction = EXCLUDED.direction" in prediction_insert_sql
    assert "confidence = EXCLUDED.confidence" in prediction_insert_sql
    assert "expected_change_percent = EXCLUDED.expected_change_percent" in prediction_insert_sql
    assert "risk_level = EXCLUDED.risk_level" in prediction_insert_sql
    assert prediction_insert_params == [
        {
            "stock_id": 42,
            "horizon": "1d",
            "forecast_run_id": 200,
            "direction": "bullish",
            "confidence": 0.68,
            "expected_change_percent": 0.8,
            "risk_level": "medium",
            "generated_at": "2026-06-02T13:18:00Z",
        }
    ]
    assert connection.commits == 1
