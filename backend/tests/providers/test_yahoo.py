from datetime import datetime, timezone
from datetime import timedelta

import pytest

from app.providers import (
    CompanyNewsItem,
    MarketDataResult,
    PricePoint,
    ProviderMissingDataError,
    ProviderMalformedDataError,
    ProviderStaleDataError,
    ProviderTransportError,
    ProviderUnsupportedStockError,
    SupportedStock,
)
from app.providers.yahoo import YahooMarketDataAdapter
from app.providers.yahoo import YahooCompanyNewsAdapter


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
                    "timestamp": [1780576200, 1780579800],
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


def test_yahoo_market_adapter_reads_chart_previous_close_when_present() -> None:
    response = yahoo_chart_response()
    meta = response["chart"]["result"][0]["meta"]
    meta.pop("previousClose")
    meta["chartPreviousClose"] = 210.5
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": response}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )

    result = adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))

    assert result.previous_close == 210.5


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


def yahoo_news_response() -> dict[str, object]:
    return {
        "news": [
            {
                "uuid": "news-1",
                "title": "Apple shares move after supplier update",
                "publisher": "Example Wire",
                "link": "https://finance.yahoo.com/news/apple-supplier-update",
                "providerPublishTime": 1780579800,
                "relatedTickers": ["AAPL"],
                "summary": "This field must not appear in normalized Company News.",
            }
        ]
    }


def test_yahoo_news_adapter_returns_compact_company_news_metadata() -> None:
    stock = SupportedStock("AAPL", "Apple Inc.", "NASDAQ")
    adapter = YahooCompanyNewsAdapter(http_client=FakeHttpClient({"search": yahoo_news_response()}))

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
    adapter = YahooCompanyNewsAdapter(http_client=FakeHttpClient({"search": response}))

    with pytest.raises(ProviderMissingDataError, match="title"):
        adapter.get_company_news(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


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

    with pytest.raises(ProviderMalformedDataError, match="close"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_market_adapter_rejects_missing_close_for_timestamp_row() -> None:
    response = yahoo_chart_response()
    response["chart"]["result"][0]["indicators"]["quote"][0]["close"][1] = None
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": response}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ProviderMissingDataError, match="close"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_market_adapter_rejects_missing_close_array_entry_for_timestamp_row() -> None:
    response = yahoo_chart_response()
    response["chart"]["result"][0]["indicators"]["quote"][0]["close"] = [214.1]
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": response}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ProviderMissingDataError, match="close"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_market_adapter_accepts_missing_optional_price_arrays() -> None:
    response = yahoo_chart_response()
    quote = response["chart"]["result"][0]["indicators"]["quote"][0]
    quote.pop("open")
    quote.pop("high")
    quote.pop("low")
    quote.pop("volume")
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": response}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )

    result = adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))

    assert result.historical_prices[-1].open is None
    assert result.historical_prices[-1].high is None
    assert result.historical_prices[-1].low is None
    assert result.historical_prices[-1].volume is None


def test_yahoo_market_adapter_rejects_boolean_numeric_values() -> None:
    response = yahoo_chart_response()
    response["chart"]["result"][0]["meta"]["regularMarketPrice"] = True
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": response}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ProviderMalformedDataError, match="regularMarketPrice"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_market_adapter_rejects_non_finite_numeric_values() -> None:
    response = yahoo_chart_response()
    response["chart"]["result"][0]["meta"]["regularMarketPrice"] = float("nan")
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": response}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ProviderMalformedDataError, match="regularMarketPrice"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_market_adapter_rejects_non_finite_optional_numeric_values() -> None:
    response = yahoo_chart_response()
    response["chart"]["result"][0]["meta"]["previousClose"] = float("inf")
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": response}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ProviderMalformedDataError, match="previousClose"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_market_adapter_rejects_non_finite_close_values() -> None:
    response = yahoo_chart_response()
    response["chart"]["result"][0]["indicators"]["quote"][0]["close"][1] = float("-inf")
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": response}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ProviderMalformedDataError, match="close"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_market_adapter_rejects_out_of_range_timestamp() -> None:
    response = yahoo_chart_response()
    response["chart"]["result"][0]["timestamp"][1] = 10**100
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": response}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ProviderMalformedDataError, match="timestamp"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_market_adapter_rejects_future_observed_timestamp() -> None:
    response = yahoo_chart_response()
    response["chart"]["result"][0]["timestamp"][1] = 1780585200
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": response}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ProviderMalformedDataError, match="future"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_market_adapter_rejects_any_future_historical_timestamp() -> None:
    response = yahoo_chart_response()
    response["chart"]["result"][0]["timestamp"] = [1780585200, 1780579800]
    adapter = YahooMarketDataAdapter(
        http_client=FakeHttpClient({"chart": response}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ProviderMalformedDataError, match="future"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_market_adapter_propagates_transport_errors() -> None:
    adapter = YahooMarketDataAdapter(http_client=FailingHttpClient())

    with pytest.raises(ProviderTransportError, match="network unavailable"):
        adapter.get_market_data(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_news_adapter_rejects_malformed_timestamp() -> None:
    response = yahoo_news_response()
    response["news"][0]["providerPublishTime"] = "1780579800"
    adapter = YahooCompanyNewsAdapter(http_client=FakeHttpClient({"search": response}))

    with pytest.raises(ProviderMalformedDataError, match="providerPublishTime"):
        adapter.get_company_news(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_news_adapter_rejects_unrelated_news_items() -> None:
    response = yahoo_news_response()
    response["news"][0]["relatedTickers"] = ["MSFT"]
    adapter = YahooCompanyNewsAdapter(http_client=FakeHttpClient({"search": response}))

    with pytest.raises(ProviderUnsupportedStockError, match="requested Stock"):
        adapter.get_company_news(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_news_adapter_rejects_malformed_related_tickers() -> None:
    response = yahoo_news_response()
    response["news"][0]["relatedTickers"] = [True]
    adapter = YahooCompanyNewsAdapter(http_client=FakeHttpClient({"search": response}))

    with pytest.raises(ProviderMalformedDataError, match="relatedTickers"):
        adapter.get_company_news(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_news_adapter_rejects_future_publish_time() -> None:
    response = yahoo_news_response()
    response["news"][0]["providerPublishTime"] = 1780585200
    adapter = YahooCompanyNewsAdapter(
        http_client=FakeHttpClient({"search": response}),
        now=lambda: datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ProviderMalformedDataError, match="future"):
        adapter.get_company_news(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))


def test_yahoo_news_adapter_propagates_transport_errors() -> None:
    adapter = YahooCompanyNewsAdapter(http_client=FailingHttpClient())

    with pytest.raises(ProviderTransportError, match="network unavailable"):
        adapter.get_company_news(SupportedStock("AAPL", "Apple Inc.", "NASDAQ"))
