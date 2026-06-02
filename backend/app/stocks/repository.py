from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol, TypedDict

from app.database.connection import open_database_connection


EXAMPLE_TICKERS = ("AAPL", "MSFT", "NVDA", "TSLA")


class StockRow(TypedDict):
    ticker: str
    company_name: str
    exchange: str


class StockSearchRepository(Protocol):
    def search(self, query: str) -> list[StockRow]: ...

    def examples(self) -> list[StockRow]: ...


def escape_like_pattern(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@dataclass
class PostgresStockSearchRepository:
    connection: object

    def search(self, query: str) -> list[StockRow]:
        normalized = query.strip().lower()
        escaped = escape_like_pattern(normalized)
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT ticker, company_name, exchange
                FROM supported_stocks
                WHERE is_supported = TRUE
                  AND search_text LIKE %(query_pattern)s ESCAPE '\\'
                ORDER BY
                  CASE
                    WHEN lower(ticker) = %(query)s THEN 0
                    WHEN lower(ticker) LIKE %(ticker_prefix)s ESCAPE '\\' THEN 1
                    ELSE 2
                  END,
                  ticker ASC
                LIMIT 10
                """,
                {
                    "query": normalized,
                    "query_pattern": f"%{escaped}%",
                    "ticker_prefix": f"{escaped}%",
                },
            )
            return [
                {"ticker": row[0], "company_name": row[1], "exchange": row[2]}
                for row in cursor.fetchall()
            ]

    def examples(self) -> list[StockRow]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT ticker, company_name, exchange
                FROM supported_stocks
                WHERE is_supported = TRUE
                  AND ticker = ANY(%(tickers)s)
                ORDER BY array_position(%(tickers)s, ticker)
                """,
                {"tickers": list(EXAMPLE_TICKERS)},
            )
            return [
                {"ticker": row[0], "company_name": row[1], "exchange": row[2]}
                for row in cursor.fetchall()
            ]


def get_stock_search_repository() -> Iterator[StockSearchRepository]:
    with open_database_connection() as connection:
        yield PostgresStockSearchRepository(connection)
