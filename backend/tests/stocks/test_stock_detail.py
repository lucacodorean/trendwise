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

    def fetchall(self) -> list[tuple[object, ...]]:
        rows = self.rows.pop(0)
        assert isinstance(rows, list)
        return rows


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
                    "historical_points": [
                        {
                            "sequence": 1,
                            "timestamp": datetime(2026, 6, 2, 12, 30, tzinfo=timezone.utc),
                            "value": 211.7,
                        },
                        {
                            "sequence": 2,
                            "timestamp": datetime(2026, 6, 2, 13, 30, tzinfo=timezone.utc),
                            "value": 214.35,
                        },
                    ],
                    "line_points": [
                        {
                            "sequence": 1,
                            "timestamp": datetime(2026, 6, 2, 14, 0, tzinfo=timezone.utc),
                            "expected_value": 215.1,
                            "lower_bound": 213.4,
                            "upper_bound": 216.8,
                        }
                    ],
                    "candlesticks": [
                        {
                            "sequence": 1,
                            "timestamp": datetime(2026, 6, 2, 14, 0, tzinfo=timezone.utc),
                            "open": 214.35,
                            "high": 216.2,
                            "low": 213.9,
                            "close": 215.1,
                        }
                    ],
                },
                "prediction": {
                    "direction": "bullish",
                    "confidence": 0.68,
                    "expected_change_percent": 0.8,
                    "risk_level": "medium",
                    "generated_at": datetime(2026, 6, 2, 13, 18, tzinfo=timezone.utc),
                    "key_factors": [
                        {
                            "factor_type": "market_snapshot",
                            "source_reference_type": "market_snapshot",
                            "source_id": 20,
                            "label": "Recent price momentum",
                            "value": 1.24,
                            "rationale": "Latest snapshot shows positive daily movement.",
                            "polarity": "positive",
                            "weight": 0.45,
                        }
                    ],
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
            [
                (
                    1,
                    datetime(2026, 6, 2, 12, 30, tzinfo=timezone.utc),
                    Decimal("211.7"),
                ),
                (
                    2,
                    datetime(2026, 6, 2, 13, 30, tzinfo=timezone.utc),
                    Decimal("214.35"),
                ),
            ],
            [
                (
                    1,
                    datetime(2026, 6, 2, 14, 0, tzinfo=timezone.utc),
                    Decimal("215.1"),
                    Decimal("213.4"),
                    Decimal("216.8"),
                )
            ],
            [
                (
                    1,
                    datetime(2026, 6, 2, 14, 0, tzinfo=timezone.utc),
                    Decimal("214.35"),
                    Decimal("216.2"),
                    Decimal("213.9"),
                    Decimal("215.1"),
                )
            ],
            (
                11,
                "bullish",
                Decimal("0.68"),
                Decimal("0.8"),
                "medium",
                prediction_generated_at,
            ),
            [
                (
                    1,
                    "market_snapshot",
                    "market_snapshot",
                    20,
                    "Recent price momentum",
                    Decimal("1.24"),
                    "Latest snapshot shows positive daily movement.",
                    "positive",
                    Decimal("0.45"),
                )
            ],
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
            "historical_points": [
                {
                    "sequence": 1,
                    "timestamp": datetime(2026, 6, 2, 12, 30, tzinfo=timezone.utc),
                    "value": 211.7,
                },
                {
                    "sequence": 2,
                    "timestamp": datetime(2026, 6, 2, 13, 30, tzinfo=timezone.utc),
                    "value": 214.35,
                },
            ],
            "line_points": [
                {
                    "sequence": 1,
                    "timestamp": datetime(2026, 6, 2, 14, 0, tzinfo=timezone.utc),
                    "expected_value": 215.1,
                    "lower_bound": 213.4,
                    "upper_bound": 216.8,
                }
            ],
            "candlesticks": [
                {
                    "sequence": 1,
                    "timestamp": datetime(2026, 6, 2, 14, 0, tzinfo=timezone.utc),
                    "open": 214.35,
                    "high": 216.2,
                    "low": 213.9,
                    "close": 215.1,
                }
            ],
        },
        "prediction": {
            "direction": "bullish",
            "confidence": 0.68,
            "expected_change_percent": 0.8,
            "risk_level": "medium",
            "generated_at": prediction_generated_at,
            "key_factors": [
                {
                    "factor_type": "market_snapshot",
                    "source_reference_type": "market_snapshot",
                    "source_id": 20,
                    "label": "Recent price momentum",
                    "value": 1.24,
                    "rationale": "Latest snapshot shows positive daily movement.",
                    "polarity": "positive",
                    "weight": 0.45,
                }
            ],
        },
    }
    assert [params for _, params in connection.cursor_instance.executed] == [
        {"ticker": "AAPL"},
        {"stock_id": 1},
        {"stock_id": 1, "horizon": "1d"},
        {"stock_id": 1},
        {"forecast_run_id": 10},
        {"forecast_run_id": 10},
        {"forecast_run_id": 10},
        {"prediction_run_id": 11},
    ]
    sql = "\n".join(query for query, _ in connection.cursor_instance.executed)
    assert "FROM stocks" in sql
    assert "FROM market_snapshots" in sql
    assert "FROM forecast_runs" in sql
    assert "ROW_NUMBER() OVER (ORDER BY observed_at ASC, id ASC)" in sql
    assert "FROM forecast_line_points" in sql
    assert "FROM forecast_candlesticks" in sql
    assert "FROM prediction_runs" in sql
    assert "FROM prediction_key_factors" in sql
    prediction_query = connection.cursor_instance.executed[6][0]
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
        "horizonMetadata": {
            "value": "1d",
            "label": "1 day",
            "timeBasis": "regular_market",
            "pricePointBasis": "trading_session",
            "calendarBasis": "regular_market_trading_time",
            "newsWindowDays": 3,
            "externalFactorWeightScale": 1.15,
            "expectedForecastPointCount": 8,
        },
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
            "historicalPoints": [
                {
                    "sequence": 1,
                    "timestamp": "2026-06-02T12:30:00Z",
                    "value": 211.7,
                },
                {
                    "sequence": 2,
                    "timestamp": "2026-06-02T13:30:00Z",
                    "value": 214.35,
                },
            ],
            "linePoints": [
                {
                    "sequence": 1,
                    "timestamp": "2026-06-02T14:00:00Z",
                    "expectedValue": 215.1,
                    "lowerBound": 213.4,
                    "upperBound": 216.8,
                }
            ],
            "candlesticks": [
                {
                    "sequence": 1,
                    "timestamp": "2026-06-02T14:00:00Z",
                    "open": 214.35,
                    "high": 216.2,
                    "low": 213.9,
                    "close": 215.1,
                }
            ],
        },
        "prediction": {
            "status": "available",
            "direction": "bullish",
            "confidence": 0.68,
            "expectedChangePercent": 0.8,
            "riskLevel": "medium",
            "generatedAt": "2026-06-02T13:18:00Z",
            "freshnessLabel": "Prediction fresh at 2026-06-02T13:18:00Z",
            "keyFactors": [
                {
                    "factorType": "market_snapshot",
                    "sourceReferenceType": "market_snapshot",
                    "sourceId": 20,
                    "label": "Recent price momentum",
                    "value": 1.24,
                    "rationale": "Latest snapshot shows positive daily movement.",
                    "polarity": "positive",
                    "weight": 0.45,
                }
            ],
        },
        "disclaimer": "Trendwise outputs are informational estimates only. They are not financial advice or trading recommendations.",
    }


def test_stock_detail_accepts_explicit_valid_horizon() -> None:
    response = client().get("/stocks/AAPL/detail", params={"horizon": "5d"})

    assert response.status_code == 200
    assert response.json()["horizon"] == "5d"


def test_stock_detail_returns_metadata_for_explicit_horizon() -> None:
    response = client().get("/stocks/AAPL/detail", params={"horizon": "1mo"})

    assert response.status_code == 200
    assert response.json()["horizon"] == "1mo"
    assert response.json()["horizonMetadata"] == {
        "value": "1mo",
        "label": "1 month",
        "timeBasis": "calendar_period",
        "pricePointBasis": "trading_session",
        "calendarBasis": "calendar_period",
        "newsWindowDays": 30,
        "externalFactorWeightScale": 0.85,
        "expectedForecastPointCount": 10,
    }


def test_stock_detail_rejects_ambiguous_horizon_values_before_repository_lookup() -> None:
    repository = FakeStockDetailRepository()

    for horizon in ("1M", "30M", "2d"):
        response = client(repository).get("/stocks/AAPL/detail", params={"horizon": horizon})

        assert response.status_code == 422

    assert repository.calls == []


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
    assert body["forecast"]["historicalPoints"] == []
    assert body["forecast"]["linePoints"] == []
    assert body["forecast"]["candlesticks"] == []
    assert body["prediction"]["status"] == "unavailable"
    assert body["prediction"]["keyFactors"] == []


def test_stock_detail_copy_does_not_use_recommendation_language() -> None:
    response = client().get("/stocks/AAPL/detail")

    body = response.json()
    copy_fields = [
        body["market"]["freshnessLabel"],
        body["forecast"]["freshnessLabel"],
        body["prediction"]["freshnessLabel"],
        *[
            factor["label"]
            for factor in body["prediction"]["keyFactors"]
        ],
        *[
            factor["rationale"]
            for factor in body["prediction"]["keyFactors"]
            if factor["rationale"] is not None
        ],
    ]
    serialized_copy = " ".join(copy_fields).lower()

    assert "buy" not in serialized_copy
    assert "sell" not in serialized_copy
    assert "hold" not in serialized_copy
    assert "recommend" not in serialized_copy
    assert body["prediction"]["direction"] == "bullish"
