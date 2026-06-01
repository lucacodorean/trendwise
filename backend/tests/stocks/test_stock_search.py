from collections.abc import Iterator

from fastapi.testclient import TestClient

from app.main import app
from app.stocks.repository import (
    PostgresStockSearchRepository,
    get_stock_search_repository,
)


class RecordingCursor:
    sql: str | None = None
    params: dict[str, str] | None = None

    def __enter__(self) -> "RecordingCursor":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, sql: str, params: dict[str, str]) -> None:
        self.sql = sql
        self.params = params

    def fetchall(self) -> list[tuple[str, str, str]]:
        return []


class RecordingConnection:
    def __init__(self) -> None:
        self.cursor_instance = RecordingCursor()

    def cursor(self) -> RecordingCursor:
        return self.cursor_instance


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


def test_postgres_stock_search_orders_exact_ticker_then_prefix_then_ticker() -> None:
    connection = RecordingConnection()
    repository = PostgresStockSearchRepository(connection)

    assert repository.search("Aa") == []

    sql = connection.cursor_instance.sql
    params = connection.cursor_instance.params

    assert sql is not None
    assert "WHEN lower(ticker) = %(query)s THEN 0" in sql
    assert "WHEN lower(ticker) LIKE %(ticker_prefix)s THEN 1" in sql
    assert "ELSE 2" in sql
    assert "ticker ASC" in sql
    assert "LIMIT 10" in sql
    assert params == {
        "query": "aa",
        "query_pattern": "%aa%",
        "ticker_prefix": "aa%",
    }
