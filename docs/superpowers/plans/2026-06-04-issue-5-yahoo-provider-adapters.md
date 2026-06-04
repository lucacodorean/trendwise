# Issue 5 Yahoo Provider Adapters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add provider interfaces and Yahoo Finance adapters that return normalized market data and compact Company News metadata without persistence writes.

**Architecture:** Create a focused `backend/app/providers/` package. Shared provider protocols, normalized dataclasses, and provider errors live in `interfaces.py`; HTTP transport lives in `http.py`; Yahoo response normalization lives in `yahoo.py`. Tests inject fake HTTP clients so no test performs a live Yahoo call.

**Tech Stack:** Python 3.9, dataclasses, typing protocols, stdlib `urllib.request`, pytest.

---

## File Structure

- Create `backend/app/providers/__init__.py`: package exports for provider consumers.
- Create `backend/app/providers/interfaces.py`: provider protocols, supported Stock input, normalized result dataclasses, and provider error classes.
- Create `backend/app/providers/http.py`: minimal JSON HTTP client protocol and stdlib implementation.
- Create `backend/app/providers/yahoo.py`: Yahoo market and Company News adapters plus normalization helpers.
- Create `backend/tests/providers/test_yahoo.py`: provider unit tests using fake HTTP clients and fixture dictionaries.
- Modify no API route, storage repository, migration, or job files for issue #5.

## Task 1: Provider Interfaces And Errors

**Files:**
- Create: `backend/app/providers/__init__.py`
- Create: `backend/app/providers/interfaces.py`
- Test: `backend/tests/providers/test_yahoo.py`

- [ ] **Step 1: Write the failing interface import test**

Add this initial test file:

```python
from datetime import datetime, timezone

from app.providers import (
    CompanyNewsItem,
    MarketDataResult,
    PricePoint,
    ProviderMalformedDataError,
    SupportedStock,
)


def test_provider_interfaces_expose_normalized_market_and_news_shapes() -> None:
    stock = SupportedStock(
        ticker="aapl",
        company_name="Apple Inc.",
        exchange="NASDAQ",
    )
    observed_at = datetime(2026, 6, 4, 13, 30, tzinfo=timezone.utc)
    point = PricePoint(
        timestamp=observed_at,
        open=213.0,
        high=215.0,
        low=212.5,
        close=214.35,
        volume=123456,
    )
    market = MarketDataResult(
        stock=stock,
        provider="yahoo",
        latest_price=214.35,
        previous_close=211.73,
        market_status="regular",
        observed_at=observed_at,
        historical_prices=[point],
    )
    news = CompanyNewsItem(
        stock=stock,
        provider="yahoo",
        title="Apple supplier update",
        url="https://finance.yahoo.com/news/apple-supplier-update",
        publisher="Example Wire",
        published_at=observed_at,
        provider_id="abc123",
    )

    assert market.stock.ticker == "AAPL"
    assert market.historical_prices == [point]
    assert news.title == "Apple supplier update"
    assert issubclass(ProviderMalformedDataError, Exception)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && python3 -m pytest tests/providers/test_yahoo.py::test_provider_interfaces_expose_normalized_market_and_news_shapes -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.providers'`.

- [ ] **Step 3: Add provider interfaces and exports**

Create `backend/app/providers/interfaces.py`:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol


@dataclass(frozen=True)
class SupportedStock:
    ticker: str
    company_name: str
    exchange: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ticker", self.ticker.strip().upper())
        object.__setattr__(self, "company_name", self.company_name.strip())
        object.__setattr__(self, "exchange", self.exchange.strip())


@dataclass(frozen=True)
class PricePoint:
    timestamp: datetime
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: float
    volume: Optional[int]


@dataclass(frozen=True)
class MarketDataResult:
    stock: SupportedStock
    provider: str
    latest_price: float
    previous_close: Optional[float]
    market_status: Optional[str]
    observed_at: datetime
    historical_prices: list[PricePoint]


@dataclass(frozen=True)
class CompanyNewsItem:
    stock: SupportedStock
    provider: str
    title: str
    url: Optional[str]
    publisher: Optional[str]
    published_at: datetime
    provider_id: Optional[str]


@dataclass(frozen=True)
class StockSummaryInput:
    stock: SupportedStock
    market_data: Optional[MarketDataResult]
    news_items: list[CompanyNewsItem]


@dataclass(frozen=True)
class StockSummaryResult:
    stock: SupportedStock
    summary: str
    generated_at: datetime


class ProviderError(Exception):
    pass


class ProviderTransportError(ProviderError):
    pass


class ProviderMissingDataError(ProviderError):
    pass


class ProviderStaleDataError(ProviderError):
    pass


class ProviderMalformedDataError(ProviderError):
    pass


class ProviderUnsupportedStockError(ProviderError):
    pass


class MarketDataProvider(Protocol):
    def get_market_data(self, stock: SupportedStock) -> MarketDataResult: ...


class CompanyNewsProvider(Protocol):
    def get_company_news(self, stock: SupportedStock) -> list[CompanyNewsItem]: ...


class SummaryProvider(Protocol):
    def generate_summary(self, summary_input: StockSummaryInput) -> StockSummaryResult: ...
```

Create `backend/app/providers/__init__.py`:

```python
from app.providers.interfaces import (
    CompanyNewsItem,
    CompanyNewsProvider,
    MarketDataProvider,
    MarketDataResult,
    PricePoint,
    ProviderError,
    ProviderMalformedDataError,
    ProviderMissingDataError,
    ProviderStaleDataError,
    ProviderTransportError,
    ProviderUnsupportedStockError,
    StockSummaryInput,
    StockSummaryResult,
    SummaryProvider,
    SupportedStock,
)

__all__ = [
    "CompanyNewsItem",
    "CompanyNewsProvider",
    "MarketDataProvider",
    "MarketDataResult",
    "PricePoint",
    "ProviderError",
    "ProviderMalformedDataError",
    "ProviderMissingDataError",
    "ProviderStaleDataError",
    "ProviderTransportError",
    "ProviderUnsupportedStockError",
    "StockSummaryInput",
    "StockSummaryResult",
    "SummaryProvider",
    "SupportedStock",
]
```

- [ ] **Step 4: Run the interface test to verify it passes**

Run: `cd backend && python3 -m pytest tests/providers/test_yahoo.py::test_provider_interfaces_expose_normalized_market_and_news_shapes -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/providers/__init__.py backend/app/providers/interfaces.py backend/tests/providers/test_yahoo.py
git commit -m "feat: add provider interfaces"
```

## Task 2: Yahoo Market Data Adapter

**Files:**
- Create: `backend/app/providers/http.py`
- Create: `backend/app/providers/yahoo.py`
- Modify: `backend/app/providers/__init__.py`
- Test: `backend/tests/providers/test_yahoo.py`

- [ ] **Step 1: Add failing Yahoo market normalization tests**

Append these tests to `backend/tests/providers/test_yahoo.py`:

```python
from datetime import timedelta

import pytest

from app.providers import ProviderMissingDataError, ProviderStaleDataError
from app.providers.yahoo import YahooMarketDataAdapter


class FakeHttpClient:
    def __init__(self, responses: dict[str, dict[str, object]]) -> None:
        self.responses = responses
        self.urls: list[str] = []

    def get_json(self, url: str) -> dict[str, object]:
        self.urls.append(url)
        for key, response in self.responses.items():
            if key in url:
                return response
        raise AssertionError(f"Unexpected URL {url}")


def yahoo_chart_response() -> dict[str, object]:
    return {
        "chart": {
            "result": [
                {
                    "meta": {
                        "symbol": "AAPL",
                        "regularMarketPrice": 214.35,
                        "previousClose": 211.73,
                        "exchangeName": "NASDAQ",
                        "instrumentType": "EQUITY",
                        "marketState": "REGULAR",
                    },
                    "timestamp": [1780579800, 1780583400],
                    "indicators": {
                        "quote": [
                            {
                                "open": [213.0, 214.0],
                                "high": [214.8, 215.0],
                                "low": [212.5, 213.8],
                                "close": [214.1, 214.35],
                                "volume": [1000, 1200],
                            }
                        ]
                    },
                }
            ],
            "error": None,
        }
    }


def test_yahoo_market_adapter_returns_normalized_market_data() -> None:
    stock = SupportedStock("AAPL", "Apple Inc.", "NASDAQ")
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": yahoo_chart_response()}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
        max_age=timedelta(hours=1),
    )

    result = adapter.get_market_data(stock)

    assert result.stock == stock
    assert result.provider == "yahoo"
    assert result.latest_price == 214.35
    assert result.previous_close == 211.73
    assert result.market_status == "regular"
    assert result.observed_at == datetime(2026, 6, 4, 13, 30, tzinfo=timezone.utc)
    assert result.historical_prices[-1].close == 214.35
    assert result.historical_prices[-1].volume == 1200


def test_yahoo_market_adapter_rejects_missing_required_market_fields() -> None:
    response = yahoo_chart_response()
    result = response["chart"]["result"][0]
    result["meta"].pop("regularMarketPrice")
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": response}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ProviderMissingDataError, match="regularMarketPrice"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_market_adapter_rejects_stale_market_data() -> None:
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": yahoo_chart_response()}),
        now=lambda: datetime(2026, 6, 4, 16, 0, tzinfo=timezone.utc),
        max_age=timedelta(minutes=30),
    )

    with pytest.raises(ProviderStaleDataError, match="stale"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))
```

- [ ] **Step 2: Run the Yahoo market tests to verify they fail**

Run: `cd backend && python3 -m pytest tests/providers/test_yahoo.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.providers.yahoo'`.

- [ ] **Step 3: Add HTTP client and Yahoo market adapter**

Create `backend/app/providers/http.py`:

```python
import json
from typing import Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.providers.interfaces import ProviderTransportError


class JsonHttpClient(Protocol):
    def get_json(self, url: str) -> dict[str, object]: ...


class UrlLibJsonHttpClient:
    def get_json(self, url: str) -> dict[str, object]:
        request = Request(url, headers={"User-Agent": "trendwise-prototype/0.1"})
        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, json.JSONDecodeError) as error:
            raise ProviderTransportError(str(error)) from error

        if not isinstance(payload, dict):
            raise ProviderTransportError("Provider returned non-object JSON")
        return payload
```

Create `backend/app/providers/yahoo.py`:

```python
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional
from urllib.parse import quote

from app.providers.http import JsonHttpClient, UrlLibJsonHttpClient
from app.providers.interfaces import (
    MarketDataResult,
    PricePoint,
    ProviderMalformedDataError,
    ProviderMissingDataError,
    ProviderStaleDataError,
    ProviderUnsupportedStockError,
    SupportedStock,
)

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=1d"


def _utc_from_epoch(value: object, field_name: str) -> datetime:
    if not isinstance(value, (int, float)):
        raise ProviderMalformedDataError(f"{field_name} must be a Unix timestamp")
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _required_number(value: object, field_name: str) -> float:
    if not isinstance(value, (int, float)):
        raise ProviderMissingDataError(field_name)
    return float(value)


def _optional_number(value: object, field_name: str) -> Optional[float]:
    if value is None:
        return None
    if not isinstance(value, (int, float)):
        raise ProviderMalformedDataError(f"{field_name} must be numeric")
    return float(value)


def _optional_int(value: object, field_name: str) -> Optional[int]:
    if value is None:
        return None
    if not isinstance(value, int):
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


def _quote_values(quote: dict[str, object], key: str) -> list[object]:
    values = quote.get(key)
    if not isinstance(values, list):
        raise ProviderMalformedDataError(f"quote.{key} must be a list")
    return values


def _market_status(value: object) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProviderMalformedDataError("marketState must be a string")
    return value.strip().lower() or None


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
        previous_close = _optional_number(meta.get("previousClose"), "previousClose")
        market_status = _market_status(meta.get("marketState"))
        historical_prices = self._historical_prices(result)
        if not historical_prices:
            raise ProviderMissingDataError("historical_prices")
        observed_at = historical_prices[-1].timestamp
        if self.now().astimezone(timezone.utc) - observed_at > self.max_age:
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
        quote = _object(quote_list[0], "indicators.quote[0]")
        opens = _quote_values(quote, "open")
        highs = _quote_values(quote, "high")
        lows = _quote_values(quote, "low")
        closes = _quote_values(quote, "close")
        volumes = _quote_values(quote, "volume")

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
```

Modify `backend/app/providers/__init__.py` to export the Yahoo market adapter:

```python
from app.providers.interfaces import (
    CompanyNewsItem,
    CompanyNewsProvider,
    MarketDataProvider,
    MarketDataResult,
    PricePoint,
    ProviderError,
    ProviderMalformedDataError,
    ProviderMissingDataError,
    ProviderStaleDataError,
    ProviderTransportError,
    ProviderUnsupportedStockError,
    StockSummaryInput,
    StockSummaryResult,
    SummaryProvider,
    SupportedStock,
)
from app.providers.yahoo import YahooMarketDataAdapter

__all__ = [
    "CompanyNewsItem",
    "CompanyNewsProvider",
    "MarketDataProvider",
    "MarketDataResult",
    "PricePoint",
    "ProviderError",
    "ProviderMalformedDataError",
    "ProviderMissingDataError",
    "ProviderStaleDataError",
    "ProviderTransportError",
    "ProviderUnsupportedStockError",
    "StockSummaryInput",
    "StockSummaryResult",
    "SummaryProvider",
    "SupportedStock",
    "YahooMarketDataAdapter",
]
```

- [ ] **Step 4: Run the Yahoo market tests to verify they pass**

Run: `cd backend && python3 -m pytest tests/providers/test_yahoo.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/providers/__init__.py backend/app/providers/http.py backend/app/providers/yahoo.py backend/tests/providers/test_yahoo.py
git commit -m "feat: normalize yahoo market data"
```

## Task 3: Yahoo Company News Adapter

**Files:**
- Modify: `backend/app/providers/yahoo.py`
- Modify: `backend/app/providers/__init__.py`
- Test: `backend/tests/providers/test_yahoo.py`

- [ ] **Step 1: Add failing Yahoo Company News tests**

Append these tests to `backend/tests/providers/test_yahoo.py`:

```python
from app.providers.yahoo import YahooCompanyNewsAdapter


def yahoo_news_response() -> dict[str, object]:
    return {
        "news": [
            {
                "uuid": "news-1",
                "title": "Apple shares move after supplier update",
                "publisher": "Example Wire",
                "link": "https://finance.yahoo.com/news/apple-supplier-update",
                "providerPublishTime": 1780579800,
                "summary": "This field must not appear in normalized Company News.",
            }
        ]
    }


def test_yahoo_news_adapter_returns_compact_company_news_metadata() -> None:
    stock = SupportedStock("AAPL", "Apple Inc.", "NASDAQ")
    adapter = YahooCompanyNewsAdapter(http_client=FakeHttpClient({"quote": yahoo_news_response()}))

    result = adapter.get_company_news(stock)

    assert result == [
        CompanyNewsItem(
            stock=stock,
            provider="yahoo",
            title="Apple shares move after supplier update",
            url="https://finance.yahoo.com/news/apple-supplier-update",
            publisher="Example Wire",
            published_at=datetime(2026, 6, 4, 13, 30, tzinfo=timezone.utc),
            provider_id="news-1",
        )
    ]
    assert not hasattr(result[0], "summary")


def test_yahoo_news_adapter_rejects_news_items_missing_required_fields() -> None:
    response = yahoo_news_response()
    response["news"][0].pop("title")
    adapter = YahooCompanyNewsAdapter(http_client=FakeHttpClient({"quote": response}))

    with pytest.raises(ProviderMissingDataError, match="title"):
        adapter.get_company_news(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))
```

- [ ] **Step 2: Run the Yahoo news tests to verify they fail**

Run: `cd backend && python3 -m pytest tests/providers/test_yahoo.py::test_yahoo_news_adapter_returns_compact_company_news_metadata tests/providers/test_yahoo.py::test_yahoo_news_adapter_rejects_news_items_missing_required_fields -v`

Expected: FAIL with `ImportError` for `YahooCompanyNewsAdapter`.

- [ ] **Step 3: Add Yahoo Company News adapter**

Modify `backend/app/providers/yahoo.py` by adding these imports and class:

```python
from app.providers.interfaces import CompanyNewsItem

YAHOO_QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}&newsCount=10"


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


@dataclass
class YahooCompanyNewsAdapter:
    http_client: JsonHttpClient = UrlLibJsonHttpClient()

    def get_company_news(self, stock: SupportedStock) -> list[CompanyNewsItem]:
        url = YAHOO_QUOTE_URL.format(ticker=quote(stock.ticker))
        payload = self.http_client.get_json(url)
        news_items = _list(payload.get("news"), "news")
        normalized: list[CompanyNewsItem] = []
        for index, item in enumerate(news_items):
            news_item = _object(item, f"news[{index}]")
            normalized.append(
                CompanyNewsItem(
                    stock=stock,
                    provider="yahoo",
                    title=_required_string(news_item.get("title"), "title"),
                    url=_optional_string(news_item.get("link"), "link"),
                    publisher=_optional_string(news_item.get("publisher"), "publisher"),
                    published_at=_utc_from_epoch(news_item.get("providerPublishTime"), "providerPublishTime"),
                    provider_id=_optional_string(news_item.get("uuid"), "uuid"),
                )
            )
        return normalized
```

Modify `backend/app/providers/__init__.py` to export `YahooCompanyNewsAdapter`:

```python
from app.providers.yahoo import YahooCompanyNewsAdapter, YahooMarketDataAdapter

__all__ = [
    "CompanyNewsItem",
    "CompanyNewsProvider",
    "MarketDataProvider",
    "MarketDataResult",
    "PricePoint",
    "ProviderError",
    "ProviderMalformedDataError",
    "ProviderMissingDataError",
    "ProviderStaleDataError",
    "ProviderTransportError",
    "ProviderUnsupportedStockError",
    "StockSummaryInput",
    "StockSummaryResult",
    "SummaryProvider",
    "SupportedStock",
    "YahooCompanyNewsAdapter",
    "YahooMarketDataAdapter",
]
```

- [ ] **Step 4: Run the provider tests to verify they pass**

Run: `cd backend && python3 -m pytest tests/providers/test_yahoo.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/providers/__init__.py backend/app/providers/yahoo.py backend/tests/providers/test_yahoo.py
git commit -m "feat: normalize yahoo company news"
```

## Task 4: Malformed, Unsupported, And Transport Coverage

**Files:**
- Modify: `backend/app/providers/yahoo.py`
- Test: `backend/tests/providers/test_yahoo.py`

- [ ] **Step 1: Add failing edge-case tests**

Append these tests to `backend/tests/providers/test_yahoo.py`:

```python
from app.providers import ProviderMalformedDataError, ProviderTransportError, ProviderUnsupportedStockError


class FailingHttpClient:
    def get_json(self, url: str) -> dict[str, object]:
        raise ProviderTransportError("network unavailable")


def test_yahoo_market_adapter_rejects_mismatched_provider_symbol() -> None:
    response = yahoo_chart_response()
    response["chart"]["result"][0]["meta"]["symbol"] = "MSFT"
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": response}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ProviderUnsupportedStockError, match="requested Stock"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_market_adapter_rejects_malformed_numeric_values() -> None:
    response = yahoo_chart_response()
    response["chart"]["result"][0]["indicators"]["quote"][0]["close"][1] = "214.35"
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": response}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ProviderMissingDataError, match="close"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_market_adapter_propagates_transport_errors() -> None:
    adapter = YahooMarketDataAdapter(http_client=FailingHttpClient())

    with pytest.raises(ProviderTransportError, match="network unavailable"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_news_adapter_rejects_malformed_timestamp() -> None:
    response = yahoo_news_response()
    response["news"][0]["providerPublishTime"] = "1780579800"
    adapter = YahooCompanyNewsAdapter(http_client=FakeHttpClient({"quote": response}))

    with pytest.raises(ProviderMalformedDataError, match="providerPublishTime"):
        adapter.get_company_news(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))
```

- [ ] **Step 2: Run edge-case tests to verify current behavior**

Run: `cd backend && python3 -m pytest tests/providers/test_yahoo.py::test_yahoo_market_adapter_rejects_mismatched_provider_symbol tests/providers/test_yahoo.py::test_yahoo_market_adapter_rejects_malformed_numeric_values tests/providers/test_yahoo.py::test_yahoo_market_adapter_propagates_transport_errors tests/providers/test_yahoo.py::test_yahoo_news_adapter_rejects_malformed_timestamp -v`

Expected: PASS if prior tasks implemented the specified error paths. If any test fails because the exception type differs, update the adapter so required missing fields raise `ProviderMissingDataError`, malformed shapes and timestamps raise `ProviderMalformedDataError`, mismatched symbols raise `ProviderUnsupportedStockError`, and HTTP failures remain `ProviderTransportError`.

- [ ] **Step 3: Run all backend tests**

Run: `cd backend && python3 -m pytest -v`

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/app/providers/yahoo.py backend/tests/providers/test_yahoo.py
git commit -m "test: cover yahoo provider edge cases"
```

## Task 5: Issue 5 Verification And Tracker Update

**Files:**
- Modify no source files unless verification exposes a defect.

- [ ] **Step 1: Verify issue #5 acceptance criteria against implementation**

Check these mappings:

- Market data, Company News, and summary generation seams are represented by `MarketDataProvider`, `CompanyNewsProvider`, and `SummaryProvider` in `backend/app/providers/interfaces.py`.
- Yahoo market adapter returns normalized historical prices, latest price, previous close, metadata identity through `SupportedStock`, and market status when present.
- Yahoo news adapter returns compact metadata through `CompanyNewsItem` and does not include raw article bodies.
- Supported Stock restriction is represented by `SupportedStock` inputs and mismatched Yahoo symbols raise `ProviderUnsupportedStockError`.
- Provider tests cover successful, missing, stale, malformed, unsupported, and transport paths.

- [ ] **Step 2: Run final verification**

Run: `cd backend && python3 -m pytest -v`

Expected: PASS.

- [ ] **Step 3: Inspect working tree**

Run: `git status --short`

Expected: no uncommitted implementation files if the task commits were made. If the design and plan docs are intentionally uncommitted, leave them visible and report that state.

- [ ] **Step 4: Update issue #5 with implementation notes**

Run this only after final verification passes:

```bash
gh issue comment 5 --body '> *This was generated by AI during triage.*

Implemented Yahoo provider adapters for issue #5.

Verification: `cd backend && python3 -m pytest -v` passed.

Follow-up ingestion persistence/job work is tracked in #23.'
```

- [ ] **Step 5: Commit tracker-note-free source state if needed**

If implementation files remain uncommitted, commit them:

```bash
git add backend/app/providers backend/tests/providers
git commit -m "feat: add yahoo provider adapters"
```

## Self-Review

- Spec coverage: Tasks cover provider interfaces, Yahoo market normalization, Yahoo Company News normalization, supported Stock boundaries, licensing-safe compact news metadata, missing/stale/malformed/unsupported/transport tests, and no persistence writes.
- Placeholder scan: no placeholders remain; each code-changing step includes concrete code or a concrete verification command.
- Type consistency: `SupportedStock`, `MarketDataResult`, `CompanyNewsItem`, provider errors, `YahooMarketDataAdapter`, and `YahooCompanyNewsAdapter` names are consistent across tasks.
