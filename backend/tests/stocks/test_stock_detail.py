from collections.abc import Iterator
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi.testclient import TestClient

from app.main import app
from app.stocks.repository import PostgresStockDetailRepository, get_stock_detail_repository


class FakeCursor:
    def __init__(self, rows: list[Optional[tuple[object, ...]]]) -> None:
        self.rows = rows
        self.executed: list[tuple[str, dict[str, object]]] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, query: str, params: dict[str, object]) -> None:
        self.executed.append((query, params))

    def fetchone(self) -> Optional[tuple[object, ...]]:
        return self.rows.pop(0)


class FakeConnection:
    def __init__(self, rows: list[Optional[tuple[object, ...]]]) -> None:
        self.cursor_instance = FakeCursor(rows)

    def cursor(self) -> FakeCursor:
        return self.cursor_instance


class FakeStockDetailRepository:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.details = {
            "ZZZZ": None,
            "MSFT": {
                "stock": {
                    "ticker": "MSFT",
                    "company_name": "Microsoft Corporation",
                    "exchange": "NASDAQ",
                },
                "market": None,
                "forecast": None,
                "prediction": None,
            },
            "AAPL": {
                "stock": {
                    "ticker": "AAPL",
                    "company_name": "Apple Inc.",
                    "exchange": "NASDAQ",
                },
                "market": {
                    "latest_price": 214.35,
                    "daily_change": 2.62,
                    "daily_change_percent": 1.24,
                    "observed_at": datetime(2026, 6, 2, 13, 30, tzinfo=timezone.utc),
                },
                "forecast": {
                    "status": "unavailable",
                    "generated_at": datetime(2026, 6, 2, 13, 15, tzinfo=timezone.utc),
                },
                "prediction": {
                    "direction": "bullish",
                    "confidence": 0.68,
                    "expected_change_percent": 0.8,
                    "risk_level": "medium",
                    "generated_at": datetime(2026, 6, 2, 13, 18, tzinfo=timezone.utc),
                },
            },
        }

    def get_detail(self, ticker: str, horizon: str):
        normalized_ticker = ticker.upper()
        self.calls.append((normalized_ticker, horizon))
        if normalized_ticker not in self.details:
            raise AssertionError(f"Unexpected detail lookup for {ticker}")
        return self.details[normalized_ticker]


def override_detail_repository(
    repository: FakeStockDetailRepository,
) -> Iterator[FakeStockDetailRepository]:
    yield repository


def client(repository: Optional[FakeStockDetailRepository] = None) -> TestClient:
    detail_repository = repository or FakeStockDetailRepository()

    def override() -> Iterator[FakeStockDetailRepository]:
        yield from override_detail_repository(detail_repository)

    app.dependency_overrides[get_stock_detail_repository] = override
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_postgres_stock_detail_repository_maps_supported_stock_detail_rows() -> None:
    observed_at = datetime(2026, 6, 2, 13, 30, tzinfo=timezone.utc)
    forecast_generated_at = datetime(2026, 6, 2, 13, 15, tzinfo=timezone.utc)
    prediction_generated_at = datetime(2026, 6, 2, 13, 18, tzinfo=timezone.utc)
    connection = FakeConnection(
        [
            (1, "AAPL", "Apple Inc.", "NASDAQ"),
            (Decimal("214.35"), Decimal("2.62"), Decimal("1.24"), observed_at),
            (10, "unavailable", forecast_generated_at),
            (
                "bullish",
                Decimal("0.68"),
                Decimal("0.8"),
                "medium",
                prediction_generated_at,
            ),
        ]
    )

    detail = PostgresStockDetailRepository(connection).get_detail(" aapl ", "1d")

    assert detail == {
        "stock": {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "exchange": "NASDAQ",
        },
        "market": {
            "latest_price": 214.35,
            "daily_change": 2.62,
            "daily_change_percent": 1.24,
            "observed_at": observed_at,
        },
        "forecast": {
            "status": "unavailable",
            "generated_at": forecast_generated_at,
        },
        "prediction": {
            "direction": "bullish",
            "confidence": 0.68,
            "expected_change_percent": 0.8,
            "risk_level": "medium",
            "generated_at": prediction_generated_at,
        },
    }
    assert [params for _, params in connection.cursor_instance.executed] == [
        {"ticker": "AAPL"},
        {"stock_id": 1},
        {"stock_id": 1, "horizon": "1d"},
        {"forecast_run_id": 10},
    ]
    sql = "\n".join(query for query, _ in connection.cursor_instance.executed)
    assert "FROM stocks" in sql
    assert "FROM market_snapshots" in sql
    assert "FROM forecast_runs" in sql
    assert "FROM prediction_runs" in sql
    prediction_query = connection.cursor_instance.executed[3][0]
    assert "forecast_run_id = %(forecast_run_id)s" in prediction_query
    assert "stock_market_details" not in sql
    assert "stock_forecast_details" not in sql
    assert "stock_prediction_details" not in sql


def test_postgres_stock_detail_repository_preserves_nullable_market_change_fields() -> None:
    observed_at = datetime(2026, 6, 2, 13, 30, tzinfo=timezone.utc)
    connection = FakeConnection(
        [
            (1, "AAPL", "Apple Inc.", "NASDAQ"),
            (Decimal("214.35"), None, None, observed_at),
            None,
            None,
        ]
    )

    detail = PostgresStockDetailRepository(connection).get_detail("AAPL", "1d")

    assert detail is not None
    assert detail["market"] == {
        "latest_price": 214.35,
        "daily_change": None,
        "daily_change_percent": None,
        "observed_at": observed_at,
    }
    prediction_query, prediction_params = connection.cursor_instance.executed[3]
    assert "stock_id = %(stock_id)s" in prediction_query
    assert "horizon = %(horizon)s" in prediction_query
    assert prediction_params == {"stock_id": 1, "horizon": "1d"}


def test_postgres_stock_detail_repository_returns_none_for_unsupported_stock() -> None:
    connection = FakeConnection([None])

    detail = PostgresStockDetailRepository(connection).get_detail("ZZZZ", "1d")

    assert detail is None
    assert [params for _, params in connection.cursor_instance.executed] == [
        {"ticker": "ZZZZ"}
    ]


def test_stock_detail_returns_seeded_supported_stock_for_default_horizon() -> None:
    response = client().get("/stocks/AAPL/detail")

    assert response.status_code == 200
    assert response.json() == {
        "stock": {
            "ticker": "AAPL",
            "companyName": "Apple Inc.",
            "exchange": "NASDAQ",
        },
        "horizon": "1d",
        "market": {
            "status": "available",
            "latestPrice": 214.35,
            "dailyChange": 2.62,
            "dailyChangePercent": 1.24,
            "observedAt": "2026-06-02T13:30:00Z",
            "freshnessLabel": "Market data fresh at 2026-06-02T13:30:00Z",
        },
        "forecast": {
            "status": "unavailable",
            "generatedAt": "2026-06-02T13:15:00Z",
            "freshnessLabel": "Forecast checked at 2026-06-02T13:15:00Z",
        },
        "prediction": {
            "status": "available",
            "direction": "bullish",
            "confidence": 0.68,
            "expectedChangePercent": 0.8,
            "riskLevel": "medium",
            "generatedAt": "2026-06-02T13:18:00Z",
            "freshnessLabel": "Prediction fresh at 2026-06-02T13:18:00Z",
        },
        "disclaimer": "Trendwise outputs are informational estimates only. They are not financial advice or trading recommendations.",
    }


def test_stock_detail_accepts_explicit_valid_horizon() -> None:
    response = client().get("/stocks/AAPL/detail", params={"horizon": "5d"})

    assert response.status_code == 200
    assert response.json()["horizon"] == "5d"


def test_stock_detail_rejects_invalid_horizon_before_repository_lookup() -> None:
    repository = FakeStockDetailRepository()

    response = client(repository).get("/stocks/AAPL/detail", params={"horizon": "2d"})

    assert response.status_code == 422
    assert repository.calls == []


def test_stock_detail_returns_404_for_unsupported_ticker() -> None:
    response = client().get("/stocks/ZZZZ/detail")

    assert response.status_code == 404
    assert response.json() == {"detail": "Supported Stock not found"}


def test_stock_detail_returns_unavailable_sections_for_missing_detail_rows() -> None:
    response = client().get("/stocks/MSFT/detail")

    assert response.status_code == 200
    body = response.json()
    assert body["market"] == {
        "status": "unavailable",
        "latestPrice": None,
        "dailyChange": None,
        "dailyChangePercent": None,
        "observedAt": None,
        "freshnessLabel": "Market data unavailable",
    }
    assert body["forecast"]["status"] == "unavailable"
    assert body["prediction"]["status"] == "unavailable"


def test_stock_detail_copy_does_not_use_recommendation_language() -> None:
    response = client().get("/stocks/AAPL/detail")

    body = response.json()
    copy_fields = [
        body["disclaimer"],
        body["market"]["freshnessLabel"],
        body["forecast"]["freshnessLabel"],
        body["prediction"]["freshnessLabel"],
    ]
    serialized_copy = " ".join(copy_fields).lower()

    assert "buy" not in serialized_copy
    assert "sell" not in serialized_copy
    assert "hold" not in serialized_copy
    assert body["prediction"]["direction"] == "bullish"
