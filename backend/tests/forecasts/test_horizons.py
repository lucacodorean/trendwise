from app.forecasts.baseline import HORIZON_STEPS
from app.forecasts.horizons import (
    CalendarBasis,
    ForecastHorizonMetadata,
    PricePointBasis,
    TimeBasis,
    all_horizon_metadata,
    get_horizon_metadata,
)
from app.forecasts.models import ForecastHorizon


def test_horizon_metadata_covers_exact_canonical_horizons() -> None:
    metadata = all_horizon_metadata()

    assert set(metadata) == set(ForecastHorizon)
    assert [item.value for item in metadata.values()] == [horizon.value for horizon in ForecastHorizon]


def test_intraday_and_short_term_horizons_use_regular_market_time() -> None:
    assert get_horizon_metadata(ForecastHorizon.thirty_minutes).time_basis == "regular_market"
    assert get_horizon_metadata(ForecastHorizon.one_day).time_basis == "regular_market"
    assert get_horizon_metadata(ForecastHorizon.five_days).time_basis == "regular_market"


def test_longer_horizons_use_calendar_periods_with_trading_session_points() -> None:
    for horizon in (
        ForecastHorizon.seven_days,
        ForecastHorizon.one_month,
        ForecastHorizon.six_months,
        ForecastHorizon.one_year,
    ):
        metadata = get_horizon_metadata(horizon)

        assert metadata.time_basis == "calendar_period"
        assert metadata.price_point_basis == "trading_session"


def test_all_horizons_use_trading_session_price_points() -> None:
    for horizon in ForecastHorizon:
        assert get_horizon_metadata(horizon).price_point_basis == "trading_session"


def test_metadata_expected_point_counts_match_baseline_schedule() -> None:
    for horizon, (expected_count, _interval) in HORIZON_STEPS.items():
        assert get_horizon_metadata(horizon).expected_forecast_point_count == expected_count


def test_one_day_metadata_values_are_explicit() -> None:
    metadata = get_horizon_metadata(ForecastHorizon.one_day)

    assert metadata == ForecastHorizonMetadata(
        value="1d",
        label="1 day",
        time_basis="regular_market",
        price_point_basis="trading_session",
        calendar_basis="regular_market_trading_time",
        news_window_days=3,
        external_factor_weight_scale=1.15,
        expected_forecast_point_count=8,
    )


def test_metadata_type_aliases_match_allowed_literal_values() -> None:
    time_basis: TimeBasis = "regular_market"
    calendar_basis: CalendarBasis = "calendar_period"
    price_point_basis: PricePointBasis = "trading_session"

    assert time_basis == "regular_market"
    assert calendar_basis == "calendar_period"
    assert price_point_basis == "trading_session"
