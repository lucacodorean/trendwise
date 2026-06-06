from datetime import datetime, timedelta, timezone
from typing import Optional, Protocol

from app.forecasts.baseline import generate_baseline_forecast
from app.forecasts.models import (
    CompanyNewsSignal,
    ExternalFactorSignal,
    ForecastCandlestick,
    ForecastHorizon,
    ForecastInput,
    ForecastLinePoint,
    ForecastPrediction,
    HistoricalPricePoint,
    KeyFactorInput,
    MarketSnapshotInput,
    StockIdentity,
)
from app.providers.interfaces import CompanyNewsItem, MarketDataResult, SupportedStock
from app.storage.repositories import PersistenceIds


DEFAULT_MAX_MARKET_SNAPSHOT_AGE = timedelta(days=2)


class ForecastPersistenceRepository(Protocol):
    def store_detailed_forecast_prediction(
        self,
        *,
        ticker: str,
        company_name: str,
        exchange: str,
        horizon: str,
        latest_price: float,
        daily_change: float,
        daily_change_percent: float,
        observed_at: datetime,
        forecast_status: str,
        forecast_generated_at: datetime,
        line_points: list[ForecastLinePoint],
        candlesticks: list[ForecastCandlestick],
        prediction: ForecastPrediction,
        prediction_generated_at: datetime,
        key_factors: list[KeyFactorInput],
        company_news_ids: list[int],
        external_factor_ids: list[int],
    ) -> PersistenceIds:
        ...


def build_forecast_input(
    *,
    stock: SupportedStock,
    horizon: ForecastHorizon,
    market_data: MarketDataResult,
    news_items: list[CompanyNewsItem],
    external_factors: list[ExternalFactorSignal],
) -> ForecastInput:
    return ForecastInput(
        stock=StockIdentity(ticker=stock.ticker, company_name=stock.company_name, exchange=stock.exchange),
        horizon=horizon,
        market_snapshot=MarketSnapshotInput(
            latest_price=market_data.latest_price,
            daily_change=_daily_change(market_data),
            daily_change_percent=_daily_change_percent(market_data),
            observed_at=market_data.observed_at,
        ),
        historical_prices=[HistoricalPricePoint(timestamp=point.timestamp, close=point.close) for point in market_data.historical_prices],
        company_news=[CompanyNewsSignal(source_id=None, title=item.title, published_at=item.published_at) for item in news_items],
        external_factors=external_factors,
    )


def generate_and_store_baseline_forecast(
    *,
    repository: ForecastPersistenceRepository,
    stock: SupportedStock,
    horizon: ForecastHorizon,
    market_data: MarketDataResult,
    news_items: list[CompanyNewsItem],
    external_factors: list[ExternalFactorSignal],
    now: Optional[datetime] = None,
) -> PersistenceIds:
    forecast_input = build_forecast_input(
        stock=stock,
        horizon=horizon,
        market_data=market_data,
        news_items=news_items,
        external_factors=external_factors,
    )
    generated = generate_baseline_forecast(
        forecast_input,
        now=now or datetime.now(timezone.utc),
        max_market_snapshot_age=DEFAULT_MAX_MARKET_SNAPSHOT_AGE,
    )

    return repository.store_detailed_forecast_prediction(
        ticker=generated.stock.ticker,
        company_name=generated.stock.company_name,
        exchange=generated.stock.exchange,
        horizon=generated.horizon.value,
        latest_price=market_data.latest_price,
        daily_change=_daily_change(market_data),
        daily_change_percent=_daily_change_percent(market_data),
        observed_at=market_data.observed_at,
        forecast_status="completed",
        forecast_generated_at=generated.generated_at,
        line_points=generated.line_points,
        candlesticks=generated.candlesticks,
        prediction=generated.prediction,
        prediction_generated_at=generated.generated_at,
        key_factors=generated.key_factors,
        company_news_ids=[],
        external_factor_ids=[factor.source_id for factor in external_factors if factor.source_id is not None],
    )


def _daily_change(market_data: MarketDataResult) -> float:
    if market_data.previous_close is None:
        return 0.0
    return round(market_data.latest_price - market_data.previous_close, 4)


def _daily_change_percent(market_data: MarketDataResult) -> float:
    if market_data.previous_close is None or market_data.previous_close <= 0:
        return 0.0
    return round(((market_data.latest_price - market_data.previous_close) / market_data.previous_close) * 100, 4)
