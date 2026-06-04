from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
from typing import Callable, Optional
from urllib.parse import quote

from app.providers.http import JsonHttpClient, UrlLibJsonHttpClient
from app.providers.interfaces import (
    CompanyNewsItem,
    MarketDataResult,
    PricePoint,
    ProviderMalformedDataError,
    ProviderMissingDataError,
    ProviderStaleDataError,
    ProviderUnsupportedStockError,
    SupportedStock,
)


YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=1d"
YAHOO_NEWS_URL = "https://query1.finance.yahoo.com/v1/finance/search?q={ticker}&newsCount=10&quotesCount=0"


def _utc_from_epoch(value: object, field_name: str) -> datetime:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProviderMalformedDataError(f"{field_name} must be a Unix timestamp")
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise ProviderMalformedDataError(f"{field_name} must be a valid Unix timestamp") from exc


def _required_number(value: object, field_name: str) -> float:
    if value is None:
        raise ProviderMissingDataError(field_name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProviderMalformedDataError(f"{field_name} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ProviderMalformedDataError(f"{field_name} must be finite")
    return number


def _optional_number(value: object, field_name: str) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProviderMalformedDataError(f"{field_name} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ProviderMalformedDataError(f"{field_name} must be finite")
    return number


def _optional_int(value: object, field_name: str) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProviderMalformedDataError(f"{field_name} must be an integer")
    return value


def _object(value: object, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ProviderMalformedDataError(f"{field_name} must be an object")
    return value


def _list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise ProviderMalformedDataError(f"{field_name} must be a list")
    return value


def _quote_values(quote_payload: dict[str, object], key: str) -> list[object]:
    values = quote_payload.get(key)
    if not isinstance(values, list):
        raise ProviderMalformedDataError(f"quote.{key} must be a list")
    return values


def _optional_quote_values(quote_payload: dict[str, object], key: str) -> list[object]:
    values = quote_payload.get(key)
    if values is None:
        return []
    if not isinstance(values, list):
        raise ProviderMalformedDataError(f"quote.{key} must be a list")
    return values


def _market_status(value: object) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProviderMalformedDataError("marketState must be a string")
    return value.strip().lower() or None


def _optional_string(value: object, field_name: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProviderMalformedDataError(f"{field_name} must be a string")
    cleaned = value.strip()
    return cleaned or None


def _required_string(value: object, field_name: str) -> str:
    cleaned = _optional_string(value, field_name)
    if cleaned is None:
        raise ProviderMissingDataError(field_name)
    return cleaned


def _ticker_set(values: list[object], field_name: str) -> set[str]:
    tickers: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise ProviderMalformedDataError(f"{field_name} must contain strings")
        cleaned = value.strip().upper()
        if cleaned:
            tickers.add(cleaned)
    return tickers


@dataclass
class YahooMarketDataAdapter:
    http_client: JsonHttpClient = UrlLibJsonHttpClient()
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)
    max_age: timedelta = timedelta(days=7)

    def get_market_data(self, stock: SupportedStock) -> MarketDataResult:
        url = YAHOO_CHART_URL.format(ticker=quote(stock.ticker))
        payload = self.http_client.get_json(url)
        result = self._chart_result(payload)
        meta = _object(result.get("meta"), "chart.result.meta")
        provider_symbol = meta.get("symbol")
        if not isinstance(provider_symbol, str) or provider_symbol.upper() != stock.ticker:
            raise ProviderUnsupportedStockError("Yahoo response did not match requested Stock")

        latest_price = _required_number(meta.get("regularMarketPrice"), "regularMarketPrice")
        previous_close = _optional_number(
            meta.get("previousClose", meta.get("chartPreviousClose")),
            "previousClose",
        )
        market_status = _market_status(meta.get("marketState"))
        historical_prices = self._historical_prices(result)
        if not historical_prices:
            raise ProviderMissingDataError("historical_prices")
        observed_at = historical_prices[-1].timestamp
        now_utc = self.now().astimezone(timezone.utc)
        if any(point.timestamp > now_utc for point in historical_prices):
            raise ProviderMalformedDataError("market data timestamp is in the future")
        if now_utc - observed_at > self.max_age:
            raise ProviderStaleDataError("market data is stale")

        return MarketDataResult(
            stock=stock,
            provider="yahoo",
            latest_price=latest_price,
            previous_close=previous_close,
            market_status=market_status,
            observed_at=observed_at,
            historical_prices=historical_prices,
        )

    def _chart_result(self, payload: dict[str, object]) -> dict[str, object]:
        chart = _object(payload.get("chart"), "chart")
        if chart.get("error") is not None:
            raise ProviderUnsupportedStockError("Yahoo chart returned an error")
        results = _list(chart.get("result"), "chart.result")
        if not results:
            raise ProviderMissingDataError("chart.result")
        return _object(results[0], "chart.result[0]")

    def _historical_prices(self, result: dict[str, object]) -> list[PricePoint]:
        timestamps = _list(result.get("timestamp"), "timestamp")
        indicators = _object(result.get("indicators"), "indicators")
        quote_list = _list(indicators.get("quote"), "indicators.quote")
        if not quote_list:
            raise ProviderMissingDataError("indicators.quote")
        quote_payload = _object(quote_list[0], "indicators.quote[0]")
        opens = _optional_quote_values(quote_payload, "open")
        highs = _optional_quote_values(quote_payload, "high")
        lows = _optional_quote_values(quote_payload, "low")
        closes = _quote_values(quote_payload, "close")
        volumes = _optional_quote_values(quote_payload, "volume")

        prices: list[PricePoint] = []
        for index, timestamp in enumerate(timestamps):
            if index >= len(closes) or closes[index] is None:
                continue
            prices.append(
                PricePoint(
                    timestamp=_utc_from_epoch(timestamp, "timestamp"),
                    open=_optional_number(opens[index] if index < len(opens) else None, "open"),
                    high=_optional_number(highs[index] if index < len(highs) else None, "high"),
                    low=_optional_number(lows[index] if index < len(lows) else None, "low"),
                    close=_required_number(closes[index], "close"),
                    volume=_optional_int(volumes[index] if index < len(volumes) else None, "volume"),
                )
            )
        return prices


@dataclass
class YahooCompanyNewsAdapter:
    http_client: JsonHttpClient = UrlLibJsonHttpClient()
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)

    def get_company_news(self, stock: SupportedStock) -> list[CompanyNewsItem]:
        url = YAHOO_NEWS_URL.format(ticker=quote(stock.ticker))
        payload = self.http_client.get_json(url)
        news_items = _list(payload.get("news"), "news")
        normalized: list[CompanyNewsItem] = []
        now_utc = self.now().astimezone(timezone.utc)
        for index, item in enumerate(news_items):
            news_item = _object(item, f"news[{index}]")
            related_tickers = _list(news_item.get("relatedTickers"), "relatedTickers")
            if stock.ticker not in _ticker_set(related_tickers, "relatedTickers"):
                raise ProviderUnsupportedStockError("Yahoo response did not match requested Stock")
            published_at = _utc_from_epoch(news_item.get("providerPublishTime"), "providerPublishTime")
            if published_at > now_utc:
                raise ProviderMalformedDataError("news timestamp is in the future")
            normalized.append(
                CompanyNewsItem(
                    stock=stock,
                    provider="yahoo",
                    title=_required_string(news_item.get("title"), "title"),
                    url=_optional_string(news_item.get("link"), "link"),
                    publisher=_optional_string(news_item.get("publisher"), "publisher"),
                    published_at=published_at,
                    provider_id=_optional_string(news_item.get("uuid"), "uuid"),
                )
            )
        return normalized
