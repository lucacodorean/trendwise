from datetime import datetime, timedelta, timezone
from inspect import signature
from typing import Any

from app.forecasts.models import ExternalFactorSignal, ForecastHorizon
from app.forecasts.pipeline import build_forecast_input, generate_and_store_baseline_forecast
from app.providers.interfaces import CompanyNewsItem, MarketDataResult, PricePoint, SupportedStock


class FakeForecastRepository:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def store_detailed_forecast_prediction(self, **kwargs: Any) -> dict[str, int]:
        self.calls.append(kwargs)
        return {"stock_id": 1, "market_snapshot_id": 2, "forecast_run_id": 3, "prediction_run_id": 4}


def test_generate_and_store_baseline_forecast_persists_provider_observed_data() -> None:
    observed_at = datetime(2026, 6, 6, 14, 30, tzinfo=timezone.utc)
    stock = SupportedStock(ticker="aapl", company_name="Apple Inc.", exchange="NASDAQ")
    market_data = MarketDataResult(
        stock=stock,
        provider="yahoo",
        latest_price=214.35,
        previous_close=211.73,
        market_status="open",
        observed_at=observed_at,
        historical_prices=[
            PricePoint(timestamp=observed_at - timedelta(days=3), open=None, high=None, low=None, close=210.00, volume=None),
            PricePoint(timestamp=observed_at - timedelta(days=2), open=None, high=None, low=None, close=211.50, volume=None),
            PricePoint(timestamp=observed_at - timedelta(days=1), open=None, high=None, low=None, close=212.00, volume=None),
            PricePoint(timestamp=observed_at, open=None, high=None, low=None, close=214.35, volume=None),
        ],
    )
    news_items = [
        CompanyNewsItem(
            stock=stock,
            provider="yahoo",
            title="Apple announces developer updates",
            url="https://example.com/apple",
            publisher="Example News",
            published_at=observed_at - timedelta(hours=6),
            provider_id="news-1",
        )
    ]
    external_factors = [
        ExternalFactorSignal(source_id=401, factor_type="macro", label="Rates unchanged", observed_at=observed_at - timedelta(days=1))
    ]
    repository = FakeForecastRepository()

    result = generate_and_store_baseline_forecast(
        repository=repository,
        stock=stock,
        horizon=ForecastHorizon.one_day,
        market_data=market_data,
        news_items=news_items,
        external_factors=external_factors,
        now=observed_at + timedelta(hours=1),
    )

    assert result["forecast_run_id"] == 3
    assert "prediction" not in signature(generate_and_store_baseline_forecast).parameters
    assert len(repository.calls) == 1
    call = repository.calls[0]
    assert call["ticker"] == "AAPL"
    assert call["company_name"] == "Apple Inc."
    assert call["exchange"] == "NASDAQ"
    assert call["horizon"] == "1d"
    assert call["latest_price"] == 214.35
    assert call["daily_change"] == 2.62
    assert call["daily_change_percent"] == 1.2374
    assert call["observed_at"] == observed_at
    assert call["forecast_status"] == "completed"
    assert call["forecast_generated_at"] == observed_at
    assert call["prediction_generated_at"] == observed_at
    assert call["line_points"]
    assert call["candlesticks"]
    assert call["prediction"].direction in {"bullish", "bearish", "neutral"}
    assert call["key_factors"]
    assert call["company_news_ids"] == []
    assert call["external_factor_ids"] == [401]


def test_build_forecast_input_applies_horizon_news_window() -> None:
    observed_at = datetime(2026, 6, 6, 14, 30, tzinfo=timezone.utc)
    stock = SupportedStock(ticker="aapl", company_name="Apple Inc.", exchange="NASDAQ")
    market_data = MarketDataResult(
        stock=stock,
        provider="yahoo",
        latest_price=214.35,
        previous_close=211.73,
        market_status="open",
        observed_at=observed_at,
        historical_prices=[
            PricePoint(timestamp=observed_at - timedelta(days=3), open=None, high=None, low=None, close=210.00, volume=None),
            PricePoint(timestamp=observed_at, open=None, high=None, low=None, close=214.35, volume=None),
        ],
    )
    recent_news = CompanyNewsItem(
        stock=stock,
        provider="yahoo",
        title="Recent Apple news",
        url="https://example.com/recent",
        publisher="Example News",
        published_at=observed_at - timedelta(hours=12),
        provider_id="recent",
    )
    older_news = CompanyNewsItem(
        stock=stock,
        provider="yahoo",
        title="Older Apple news",
        url="https://example.com/older",
        publisher="Example News",
        published_at=observed_at - timedelta(days=2),
        provider_id="older",
    )

    thirty_minute_input = build_forecast_input(
        stock=stock,
        horizon=ForecastHorizon.thirty_minutes,
        market_data=market_data,
        news_items=[recent_news, older_news],
        external_factors=[],
    )
    one_month_input = build_forecast_input(
        stock=stock,
        horizon=ForecastHorizon.one_month,
        market_data=market_data,
        news_items=[recent_news, older_news],
        external_factors=[],
    )

    assert [item.title for item in thirty_minute_input.company_news] == ["Recent Apple news"]
    assert [item.title for item in one_month_input.company_news] == ["Recent Apple news", "Older Apple news"]
