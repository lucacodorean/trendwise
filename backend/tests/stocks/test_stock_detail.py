from collections.abc import Iterator
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.stocks.repository import get_stock_detail_repository


class FakeStockDetailRepository:
    def get_detail(self, ticker: str, horizon: str):
        if ticker.upper() == "ZZZZ":
            return None
        if ticker.upper() == "MSFT":
            return {
                "stock": {
                    "ticker": "MSFT",
                    "company_name": "Microsoft Corporation",
                    "exchange": "NASDAQ",
                },
                "market": None,
                "forecast": None,
                "prediction": None,
            }
        return {
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
        }


def override_detail_repository() -> Iterator[FakeStockDetailRepository]:
    yield FakeStockDetailRepository()


def client() -> TestClient:
    app.dependency_overrides[get_stock_detail_repository] = override_detail_repository
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


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
    response = client().get("/stocks/AAPL/detail", params={"horizon": "2d"})

    assert response.status_code == 422


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

    serialized = str(response.json()).lower()

    assert "buy" not in serialized
    assert "sell" not in serialized
    assert "hold" not in serialized
    assert "bullish" in serialized
