from dataclasses import dataclass
from typing import Literal

from app.forecasts.baseline import HORIZON_STEPS
from app.forecasts.models import ForecastHorizon


TimeBasis = Literal["regular_market", "calendar_period"]
CalendarBasis = Literal["regular_market_trading_time", "calendar_period"]
PricePointBasis = Literal["trading_session"]


@dataclass(frozen=True)
class ForecastHorizonMetadata:
    value: str
    label: str
    time_basis: TimeBasis
    price_point_basis: PricePointBasis
    calendar_basis: CalendarBasis
    news_window_days: int
    external_factor_weight_scale: float
    expected_forecast_point_count: int


HORIZON_METADATA: dict[ForecastHorizon, ForecastHorizonMetadata] = {
    ForecastHorizon.thirty_minutes: ForecastHorizonMetadata(
        value="30m",
        label="30 min",
        time_basis="regular_market",
        price_point_basis="trading_session",
        calendar_basis="regular_market_trading_time",
        news_window_days=1,
        external_factor_weight_scale=1.25,
        expected_forecast_point_count=HORIZON_STEPS[ForecastHorizon.thirty_minutes][0],
    ),
    ForecastHorizon.one_day: ForecastHorizonMetadata(
        value="1d",
        label="1 day",
        time_basis="regular_market",
        price_point_basis="trading_session",
        calendar_basis="regular_market_trading_time",
        news_window_days=3,
        external_factor_weight_scale=1.15,
        expected_forecast_point_count=HORIZON_STEPS[ForecastHorizon.one_day][0],
    ),
    ForecastHorizon.five_days: ForecastHorizonMetadata(
        value="5d",
        label="5 days",
        time_basis="regular_market",
        price_point_basis="trading_session",
        calendar_basis="regular_market_trading_time",
        news_window_days=7,
        external_factor_weight_scale=1.0,
        expected_forecast_point_count=HORIZON_STEPS[ForecastHorizon.five_days][0],
    ),
    ForecastHorizon.seven_days: ForecastHorizonMetadata(
        value="7d",
        label="7 days",
        time_basis="calendar_period",
        price_point_basis="trading_session",
        calendar_basis="calendar_period",
        news_window_days=10,
        external_factor_weight_scale=0.95,
        expected_forecast_point_count=HORIZON_STEPS[ForecastHorizon.seven_days][0],
    ),
    ForecastHorizon.one_month: ForecastHorizonMetadata(
        value="1mo",
        label="1 month",
        time_basis="calendar_period",
        price_point_basis="trading_session",
        calendar_basis="calendar_period",
        news_window_days=30,
        external_factor_weight_scale=0.85,
        expected_forecast_point_count=HORIZON_STEPS[ForecastHorizon.one_month][0],
    ),
    ForecastHorizon.six_months: ForecastHorizonMetadata(
        value="6mo",
        label="6 months",
        time_basis="calendar_period",
        price_point_basis="trading_session",
        calendar_basis="calendar_period",
        news_window_days=90,
        external_factor_weight_scale=0.7,
        expected_forecast_point_count=HORIZON_STEPS[ForecastHorizon.six_months][0],
    ),
    ForecastHorizon.one_year: ForecastHorizonMetadata(
        value="1y",
        label="1 year",
        time_basis="calendar_period",
        price_point_basis="trading_session",
        calendar_basis="calendar_period",
        news_window_days=180,
        external_factor_weight_scale=0.6,
        expected_forecast_point_count=HORIZON_STEPS[ForecastHorizon.one_year][0],
    ),
}


def get_horizon_metadata(horizon: ForecastHorizon) -> ForecastHorizonMetadata:
    return HORIZON_METADATA[horizon]


def all_horizon_metadata() -> dict[ForecastHorizon, ForecastHorizonMetadata]:
    return dict(HORIZON_METADATA)
