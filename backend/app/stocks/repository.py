from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Protocol, TypedDict

from app.database.connection import open_database_connection


EXAMPLE_TICKERS = ("AAPL", "MSFT", "NVDA", "TSLA")


class StockRow(TypedDict):
    ticker: str
    company_name: str
    exchange: str


class StockMarketDetailRow(TypedDict):
    latest_price: float
    daily_change: Optional[float]
    daily_change_percent: Optional[float]
    observed_at: datetime


class StockForecastDetailRow(TypedDict):
    id: int
    status: str
    generated_at: datetime
    historical_points: list["StockForecastHistoricalPointRow"]
    line_points: list["StockForecastLinePointRow"]
    candlesticks: list["StockForecastCandlestickRow"]


class StockForecastHistoricalPointRow(TypedDict):
    sequence: int
    timestamp: datetime
    value: float


class StockForecastLinePointRow(TypedDict):
    sequence: int
    timestamp: datetime
    expected_value: float
    lower_bound: float
    upper_bound: float


class StockForecastCandlestickRow(TypedDict):
    sequence: int
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


class StockPredictionDetailRow(TypedDict):
    direction: str
    confidence: float
    expected_change_percent: float
    risk_level: str
    generated_at: datetime
    key_factors: list["StockDetailKeyFactorRow"]


class StockDetailKeyFactorRow(TypedDict):
    factor_type: str
    source_reference_type: Optional[str]
    source_id: Optional[int]
    label: str
    value: Optional[float]
    rationale: Optional[str]
    polarity: str
    weight: Optional[float]


class StockDetailRow(TypedDict):
    stock: StockRow
    market: Optional[StockMarketDetailRow]
    forecast: Optional[StockForecastDetailRow]
    prediction: Optional[StockPredictionDetailRow]


class StockSearchRepository(Protocol):
    def search(self, query: str) -> list[StockRow]: ...

    def examples(self) -> list[StockRow]: ...


class StockDetailRepository(Protocol):
    def get_detail(self, ticker: str, horizon: str) -> Optional[StockDetailRow]: ...


def escape_like_pattern(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def numeric_to_float(value: object) -> float:
    if isinstance(value, Decimal):
        return float(value)
    return float(value)  # type: ignore[arg-type]


def optional_numeric_to_float(value: object) -> Optional[float]:
    if value is None:
        return None
    return numeric_to_float(value)


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
                FROM stocks
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
                FROM stocks
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


@dataclass
class PostgresStockDetailRepository:
    connection: object

    def get_detail(self, ticker: str, horizon: str) -> Optional[StockDetailRow]:
        normalized_ticker = ticker.strip().upper()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, ticker, company_name, exchange
                FROM stocks
                WHERE is_supported = TRUE
                  AND ticker = %(ticker)s
                """,
                {"ticker": normalized_ticker},
            )
            stock = cursor.fetchone()
            if stock is None:
                return None
            stock_id = stock[0]

            cursor.execute(
                """
                SELECT latest_price, daily_change, daily_change_percent, observed_at
                FROM market_snapshots
                WHERE stock_id = %(stock_id)s
                ORDER BY observed_at DESC, id DESC
                LIMIT 1
                """,
                {"stock_id": stock_id},
            )
            market = cursor.fetchone()

            cursor.execute(
                """
                SELECT id, status, generated_at
                FROM forecast_runs
                WHERE stock_id = %(stock_id)s
                  AND horizon = %(horizon)s
                ORDER BY generated_at DESC, id DESC
                LIMIT 1
                """,
                {"stock_id": stock_id, "horizon": horizon},
            )
            forecast = cursor.fetchone()

            historical_points: list[StockForecastHistoricalPointRow] = []
            line_points: list[StockForecastLinePointRow] = []
            candlesticks: list[StockForecastCandlestickRow] = []
            if forecast is not None:
                cursor.execute(
                    """
                    SELECT sequence, observed_at, latest_price
                    FROM (
                        SELECT
                            ROW_NUMBER() OVER (ORDER BY observed_at ASC, id ASC) AS sequence,
                            observed_at,
                            latest_price
                        FROM (
                            SELECT ms.id, ms.observed_at, ms.latest_price
                            FROM market_snapshots ms
                            CROSS JOIN (
                                SELECT MIN(timestamp) AS timestamp
                                FROM forecast_line_points
                                WHERE forecast_run_id = %(forecast_run_id)s
                            ) first_forecast_point
                            WHERE ms.stock_id = %(stock_id)s
                              AND (
                                  ms.observed_at < first_forecast_point.timestamp
                                  OR (
                                      first_forecast_point.timestamp IS NULL
                                      AND ms.observed_at <= %(forecast_generated_at)s
                                  )
                              )
                            ORDER BY ms.observed_at DESC, ms.id DESC
                            LIMIT 8
                        ) recent_market_snapshots
                    ) ordered_market_snapshots
                    ORDER BY sequence ASC
                    """,
                    {
                        "stock_id": stock_id,
                        "forecast_run_id": forecast[0],
                        "forecast_generated_at": forecast[2],
                    },
                )
                historical_points = [
                    {
                        "sequence": row[0],
                        "timestamp": row[1],
                        "value": numeric_to_float(row[2]),
                    }
                    for row in cursor.fetchall()
                ]

                cursor.execute(
                    """
                    SELECT sequence, timestamp, expected_value, lower_bound, upper_bound
                    FROM forecast_line_points
                    WHERE forecast_run_id = %(forecast_run_id)s
                    ORDER BY sequence ASC
                    """,
                    {"forecast_run_id": forecast[0]},
                )
                line_points = [
                    {
                        "sequence": row[0],
                        "timestamp": row[1],
                        "expected_value": numeric_to_float(row[2]),
                        "lower_bound": numeric_to_float(row[3]),
                        "upper_bound": numeric_to_float(row[4]),
                    }
                    for row in cursor.fetchall()
                ]

                cursor.execute(
                    """
                    SELECT sequence, timestamp, open_price, high_price, low_price, close_price
                    FROM forecast_candlesticks
                    WHERE forecast_run_id = %(forecast_run_id)s
                    ORDER BY sequence ASC
                    """,
                    {"forecast_run_id": forecast[0]},
                )
                candlesticks = [
                    {
                        "sequence": row[0],
                        "timestamp": row[1],
                        "open": numeric_to_float(row[2]),
                        "high": numeric_to_float(row[3]),
                        "low": numeric_to_float(row[4]),
                        "close": numeric_to_float(row[5]),
                    }
                    for row in cursor.fetchall()
                ]

            if forecast is None:
                cursor.execute(
                    """
                    SELECT id, direction, confidence, expected_change_percent, risk_level, generated_at
                    FROM prediction_runs
                    WHERE stock_id = %(stock_id)s
                      AND horizon = %(horizon)s
                    ORDER BY generated_at DESC, id DESC
                    LIMIT 1
                    """,
                    {"stock_id": stock_id, "horizon": horizon},
                )
            else:
                cursor.execute(
                    """
                    SELECT id, direction, confidence, expected_change_percent, risk_level, generated_at
                    FROM prediction_runs
                    WHERE forecast_run_id = %(forecast_run_id)s
                    ORDER BY generated_at DESC, id DESC
                    LIMIT 1
                    """,
                    {"forecast_run_id": forecast[0]},
                )
            prediction = cursor.fetchone()

            key_factors: list[StockDetailKeyFactorRow] = []
            if prediction is not None:
                cursor.execute(
                    """
                    SELECT
                        sequence,
                        factor_type,
                        source_reference_type,
                        source_id,
                        label,
                        numeric_value,
                        rationale,
                        polarity,
                        weight
                    FROM prediction_key_factors
                    WHERE prediction_run_id = %(prediction_run_id)s
                    ORDER BY sequence ASC
                    """,
                    {"prediction_run_id": prediction[0]},
                )
                key_factors = [
                    {
                        "factor_type": row[1],
                        "source_reference_type": row[2],
                        "source_id": row[3],
                        "label": row[4],
                        "value": optional_numeric_to_float(row[5]),
                        "rationale": row[6],
                        "polarity": row[7],
                        "weight": optional_numeric_to_float(row[8]),
                    }
                    for row in cursor.fetchall()
                ]

        return {
            "stock": {
                "ticker": stock[1],
                "company_name": stock[2],
                "exchange": stock[3],
            },
            "market": None
            if market is None
            else {
                "latest_price": numeric_to_float(market[0]),
                "daily_change": optional_numeric_to_float(market[1]),
                "daily_change_percent": optional_numeric_to_float(market[2]),
                "observed_at": market[3],
            },
            "forecast": None
            if forecast is None
            else {
                "status": forecast[1],
                "generated_at": forecast[2],
                "historical_points": historical_points,
                "line_points": line_points,
                "candlesticks": candlesticks,
            },
            "prediction": None
            if prediction is None
            else {
                "direction": prediction[1],
                "confidence": numeric_to_float(prediction[2]),
                "expected_change_percent": numeric_to_float(prediction[3]),
                "risk_level": prediction[4],
                "generated_at": prediction[5],
                "key_factors": key_factors,
            },
        }

def get_stock_search_repository() -> Iterator[StockSearchRepository]:
    with open_database_connection() as connection:
        yield PostgresStockSearchRepository(connection)


def get_stock_detail_repository() -> Iterator[StockDetailRepository]:
    with open_database_connection() as connection:
        yield PostgresStockDetailRepository(connection)
