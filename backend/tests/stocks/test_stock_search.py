from collections.abc import Iterator

from fastapi.testclient import TestClient

from app.main import app
from app.stocks.repository import get_stock_search_repository


class FakeStockSearchRepository:
    def search(self, query: str):
        rows = [
            {"ticker": "AAPL", "company_name": "Apple Inc.", "exchange": "NASDAQ"},
            {"ticker": "MSFT", "company_name": "Microsoft Corporation", "exchange": "NASDAQ"},
            {"ticker": "AAP", "company_name": "Advance Auto Parts", "exchange": "NYSE"},
        ]
        normalized = query.strip().lower()
        if normalized == "apple":
            return [rows[0]]
        if normalized == "aa":
            return [rows[2], rows[0]]
        return []

    def examples(self):
        return [
            {"ticker": "AAPL", "company_name": "Apple Inc.", "exchange": "NASDAQ"},
            {"ticker": "MSFT", "company_name": "Microsoft Corporation", "exchange": "NASDAQ"},
        ]


def override_repository() -> Iterator[FakeStockSearchRepository]:
    yield FakeStockSearchRepository()


def client() -> TestClient:
    app.dependency_overrides[get_stock_search_repository] = override_repository
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_stock_search_returns_company_name_matches() -> None:
    response = client().get("/stocks/search", params={"q": "apple"})

    assert response.status_code == 200
    assert response.json() == {
        "results": [
            {"ticker": "AAPL", "companyName": "Apple Inc.", "exchange": "NASDAQ"}
        ]
    }


def test_stock_search_returns_fixed_examples_for_empty_query() -> None:
    response = client().get("/stocks/search", params={"q": "   "})

    assert response.status_code == 200
    assert response.json() == {
        "results": [
            {"ticker": "AAPL", "companyName": "Apple Inc.", "exchange": "NASDAQ"},
            {"ticker": "MSFT", "companyName": "Microsoft Corporation", "exchange": "NASDAQ"},
        ]
    }


def test_stock_search_preserves_repository_order_for_ticker_priority() -> None:
    response = client().get("/stocks/search", params={"q": "aa"})

    assert response.status_code == 200
    assert [row["ticker"] for row in response.json()["results"]] == ["AAP", "AAPL"]
