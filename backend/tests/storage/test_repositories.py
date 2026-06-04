from datetime import datetime, timezone
from typing import Optional

import pytest

from app.storage.repositories import PostgresPersistenceRepository


def store_snapshot_forecast_prediction(
    repository: PostgresPersistenceRepository,
) -> dict[str, int]:
    observed_at = datetime(2026, 6, 3, 13, 30, tzinfo=timezone.utc)
    generated_at = datetime(2026, 6, 3, 14, 0, tzinfo=timezone.utc)

    return repository.store_snapshot_forecast_prediction(
        ticker="aapl",
        company_name="Apple Inc.",
        exchange="NASDAQ",
        horizon="1d",
        latest_price=214.35,
        daily_change=2.62,
        daily_change_percent=1.24,
        observed_at=observed_at,
        forecast_status="unavailable",
        forecast_generated_at=generated_at,
        prediction_direction="bullish",
        prediction_confidence=0.68,
        prediction_expected_change_percent=0.8,
        prediction_risk_level="medium",
        prediction_generated_at=generated_at,
    )


class RecordingCursor:
    def __init__(self) -> None:
        self.executions = []
        self.return_values = [(101,), (201,), (301,), (401,)]
        self.fail_on_execution: Optional[int] = None

    def execute(self, sql: str, params: object = None) -> None:
        if self.fail_on_execution == len(self.executions) + 1:
            raise RuntimeError("cursor failure")
        self.executions.append((sql, params))

    def fetchone(self):
        return self.return_values.pop(0)

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None


class RecordingConnection:
    def __init__(self) -> None:
        self.cursor_instance = RecordingCursor()
        self.commits = 0
        self.rollbacks = 0

    def cursor(self) -> RecordingCursor:
        return self.cursor_instance

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def test_repository_stores_snapshot_forecast_and_prediction_round_trip() -> None:
    connection = RecordingConnection()
    repository = PostgresPersistenceRepository(connection)

    result = store_snapshot_forecast_prediction(repository)

    assert result == {
        "stock_id": 101,
        "market_snapshot_id": 201,
        "forecast_run_id": 301,
        "prediction_run_id": 401,
    }
    stock_sql, stock_params = connection.cursor_instance.executions[0]
    assert "INSERT INTO stocks" in stock_sql
    assert "ON CONFLICT (ticker) DO UPDATE" in stock_sql
    assert "RETURNING id" in stock_sql
    assert stock_params["ticker"] == "AAPL"
    assert stock_params["instrument_type"] == "common_stock"
    assert stock_params["region"] == "US"
    assert stock_params["is_supported"] is True
    assert stock_params["search_text"] == "aapl apple inc. nasdaq"

    market_sql, _ = connection.cursor_instance.executions[1]
    assert "INSERT INTO market_snapshots" in market_sql
    assert "ON CONFLICT (stock_id, provider, observed_at) DO UPDATE" in market_sql
    assert "RETURNING id" in market_sql

    forecast_sql, _ = connection.cursor_instance.executions[2]
    assert "INSERT INTO forecast_runs" in forecast_sql
    assert "ON CONFLICT (stock_id, horizon, generated_at) DO UPDATE" in forecast_sql
    assert "RETURNING id" in forecast_sql

    source_link_sql, _ = connection.cursor_instance.executions[3]
    assert "INSERT INTO forecast_source_market_snapshots" in source_link_sql
    assert (
        "ON CONFLICT (forecast_run_id, market_snapshot_id) DO NOTHING" in source_link_sql
    )

    prediction_sql, _ = connection.cursor_instance.executions[4]
    assert "INSERT INTO prediction_runs" in prediction_sql
    assert (
        "ON CONFLICT (stock_id, horizon, forecast_run_id, generated_at) DO UPDATE"
        in prediction_sql
    )
    assert "RETURNING id" in prediction_sql
    assert connection.commits == 1


def test_repository_retrieves_snapshot_forecast_and_prediction_for_stock_horizon() -> None:
    connection = RecordingConnection()
    connection.cursor_instance.return_values = [
        (
            101,
            "AAPL",
            "Apple Inc.",
            "NASDAQ",
            201,
            301,
            "1d",
            401,
        )
    ]
    repository = PostgresPersistenceRepository(connection)

    result = repository.get_snapshot_forecast_prediction(" aapl ", "1d")

    assert result == {
        "stock_id": 101,
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "exchange": "NASDAQ",
        "market_snapshot_id": 201,
        "forecast_run_id": 301,
        "horizon": "1d",
        "prediction_run_id": 401,
    }
    sql, params = connection.cursor_instance.executions[0]
    assert "FROM stocks" in sql
    assert "JOIN forecast_runs" in sql
    assert "JOIN forecast_source_market_snapshots" in sql
    assert "JOIN market_snapshots" in sql
    assert "LEFT JOIN prediction_runs" in sql
    assert "s.ticker = %(ticker)s" in sql
    assert "fr.horizon = %(horizon)s" in sql
    assert params == {"ticker": "AAPL", "horizon": "1d"}


def test_repository_rolls_back_and_reraises_when_statement_fails() -> None:
    connection = RecordingConnection()
    connection.cursor_instance.fail_on_execution = 2
    repository = PostgresPersistenceRepository(connection)

    with pytest.raises(RuntimeError, match="cursor failure"):
        store_snapshot_forecast_prediction(repository)

    assert connection.rollbacks == 1
    assert connection.commits == 0
