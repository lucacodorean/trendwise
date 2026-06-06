import math
from datetime import datetime, timedelta, timezone

import pytest

from app.forecasts.baseline import ForecastInputError, generate_baseline_forecast
from app.forecasts.models import (
    CompanyNewsSignal,
    ExternalFactorSignal,
    ForecastHorizon,
    ForecastInput,
    HistoricalPricePoint,
    MarketSnapshotInput,
    StockIdentity,
)
from app.stocks.schemas import ForecastHorizon as StockSchemaForecastHorizon


def build_input(horizon: ForecastHorizon = ForecastHorizon.one_day) -> ForecastInput:
    observed_at = datetime(2026, 6, 6, 14, 30, tzinfo=timezone.utc)
    return ForecastInput(
        stock=StockIdentity(ticker="AAPL", company_name="Apple Inc.", exchange="NASDAQ"),
        horizon=horizon,
        market_snapshot=MarketSnapshotInput(
            latest_price=214.35,
            daily_change=2.62,
            daily_change_percent=1.24,
            observed_at=observed_at,
            source_id=201,
        ),
        historical_prices=[
            HistoricalPricePoint(timestamp=observed_at - timedelta(days=3), close=210.00),
            HistoricalPricePoint(timestamp=observed_at - timedelta(days=2), close=211.50),
            HistoricalPricePoint(timestamp=observed_at - timedelta(days=1), close=212.00),
            HistoricalPricePoint(timestamp=observed_at, close=214.35),
        ],
        company_news=[
            CompanyNewsSignal(source_id=301, title="Apple announces developer updates", published_at=observed_at - timedelta(hours=6)),
        ],
        external_factors=[
            ExternalFactorSignal(source_id=401, factor_type="macro", label="Rates unchanged", observed_at=observed_at - timedelta(days=1)),
        ],
    )


def test_forecast_input_exposes_observed_sources_without_prior_predictions() -> None:
    field_names = set(ForecastInput.__dataclass_fields__)

    assert field_names == {
        "stock",
        "horizon",
        "market_snapshot",
        "historical_prices",
        "company_news",
        "external_factors",
    }
    assert "prediction" not in field_names
    assert "prediction_run" not in field_names


def test_stock_schema_uses_forecast_domain_horizon() -> None:
    assert StockSchemaForecastHorizon is ForecastHorizon


def test_generate_baseline_forecast_returns_model_compatible_output() -> None:
    result = generate_baseline_forecast(build_input())

    assert result.horizon is ForecastHorizon.one_day
    assert result.horizon.value == "1d"
    assert result.generated_at == datetime(2026, 6, 6, 14, 30, tzinfo=timezone.utc)
    assert len(result.line_points) > 0
    assert len(result.candlesticks) == len(result.line_points)
    assert result.prediction.direction in {"bullish", "bearish", "neutral"}
    assert 0 <= result.prediction.confidence <= 1
    assert result.prediction.risk_level in {"low", "medium", "high"}
    assert result.key_factors


@pytest.mark.parametrize(
    ("horizon", "expected_count"),
    [
        (ForecastHorizon.thirty_minutes, 6),
        (ForecastHorizon.one_day, 8),
        (ForecastHorizon.five_days, 5),
        (ForecastHorizon.seven_days, 7),
        (ForecastHorizon.one_month, 10),
        (ForecastHorizon.six_months, 12),
        (ForecastHorizon.one_year, 12),
    ],
)
def test_all_canonical_horizons_generate_valid_line_points(horizon: ForecastHorizon, expected_count: int) -> None:
    result = generate_baseline_forecast(build_input(horizon))

    assert len(result.line_points) == expected_count
    for index, point in enumerate(result.line_points, start=1):
        assert point.sequence == index
        assert point.timestamp > result.generated_at
        assert point.lower_bound <= point.expected_value <= point.upper_bound


def test_candlesticks_are_derived_from_expected_path_and_uncertainty() -> None:
    source = build_input(ForecastHorizon.one_day)
    result = generate_baseline_forecast(source)

    first_candle = result.candlesticks[0]
    assert first_candle.open == source.market_snapshot.latest_price
    assert first_candle.close == result.line_points[0].expected_value
    assert first_candle.high >= max(first_candle.open, first_candle.close)
    assert first_candle.low <= min(first_candle.open, first_candle.close)

    second_candle = result.candlesticks[1]
    assert second_candle.open == result.line_points[0].expected_value
    assert second_candle.close == result.line_points[1].expected_value


def test_short_history_generates_neutral_wider_uncertainty_forecast() -> None:
    source = build_input(ForecastHorizon.one_day)
    short_history_input = ForecastInput(
        stock=source.stock,
        horizon=source.horizon,
        market_snapshot=source.market_snapshot,
        historical_prices=[],
        company_news=[],
        external_factors=[],
    )

    result = generate_baseline_forecast(short_history_input)

    assert result.prediction.direction == "neutral"
    assert result.prediction.confidence <= 0.4
    assert result.prediction.risk_level == "high"
    assert result.line_points[-1].upper_bound - result.line_points[-1].lower_bound > 0


def test_non_positive_historical_close_raises_input_error() -> None:
    source = build_input(ForecastHorizon.one_day)
    malformed_input = ForecastInput(
        stock=source.stock,
        horizon=source.horizon,
        market_snapshot=source.market_snapshot,
        historical_prices=[
            source.historical_prices[0],
            HistoricalPricePoint(timestamp=source.market_snapshot.observed_at - timedelta(days=2), close=0),
        ],
        company_news=source.company_news,
        external_factors=source.external_factors,
    )

    with pytest.raises(ForecastInputError, match="Historical close prices must be positive"):
        generate_baseline_forecast(malformed_input)


@pytest.mark.parametrize("close", [math.nan, math.inf])
def test_non_finite_historical_close_raises_input_error(close: float) -> None:
    source = build_input(ForecastHorizon.one_day)
    malformed_input = ForecastInput(
        stock=source.stock,
        horizon=source.horizon,
        market_snapshot=source.market_snapshot,
        historical_prices=[
            source.historical_prices[0],
            HistoricalPricePoint(timestamp=source.market_snapshot.observed_at - timedelta(days=2), close=close),
        ],
        company_news=source.company_news,
        external_factors=source.external_factors,
    )

    with pytest.raises(ForecastInputError, match="Historical close prices must be finite"):
        generate_baseline_forecast(malformed_input)


@pytest.mark.parametrize("latest_price", [math.nan, math.inf, -math.inf])
def test_non_finite_latest_price_raises_input_error(latest_price: float) -> None:
    source = build_input(ForecastHorizon.one_day)
    malformed_input = ForecastInput(
        stock=source.stock,
        horizon=source.horizon,
        market_snapshot=MarketSnapshotInput(
            latest_price=latest_price,
            daily_change=source.market_snapshot.daily_change,
            daily_change_percent=source.market_snapshot.daily_change_percent,
            observed_at=source.market_snapshot.observed_at,
            source_id=source.market_snapshot.source_id,
        ),
        historical_prices=source.historical_prices,
        company_news=source.company_news,
        external_factors=source.external_factors,
    )

    with pytest.raises(ForecastInputError, match="Latest observed price must be finite"):
        generate_baseline_forecast(malformed_input)


@pytest.mark.parametrize("latest_price", [0, -1])
def test_non_positive_latest_price_raises_input_error(latest_price: float) -> None:
    source = build_input(ForecastHorizon.one_day)
    malformed_input = ForecastInput(
        stock=source.stock,
        horizon=source.horizon,
        market_snapshot=MarketSnapshotInput(
            latest_price=latest_price,
            daily_change=source.market_snapshot.daily_change,
            daily_change_percent=source.market_snapshot.daily_change_percent,
            observed_at=source.market_snapshot.observed_at,
            source_id=source.market_snapshot.source_id,
        ),
        historical_prices=source.historical_prices,
        company_news=source.company_news,
        external_factors=source.external_factors,
    )

    with pytest.raises(ForecastInputError, match="Latest observed price must be positive"):
        generate_baseline_forecast(malformed_input)


def test_stale_market_snapshot_raises_when_max_age_is_supplied() -> None:
    source = build_input(ForecastHorizon.one_day)

    with pytest.raises(ForecastInputError, match="Market snapshot is stale"):
        generate_baseline_forecast(
            source,
            now=source.market_snapshot.observed_at + timedelta(days=3),
            max_market_snapshot_age=timedelta(days=2),
        )


def test_generated_labels_do_not_use_recommendation_language() -> None:
    result = generate_baseline_forecast(build_input())
    labels = " ".join(factor.label for factor in result.key_factors).lower()
    rationales = " ".join(factor.rationale or "" for factor in result.key_factors).lower()
    generated_copy = f"{labels} {rationales}"

    assert "buy" not in generated_copy
    assert "sell" not in generated_copy
    assert "hold" not in generated_copy
    assert "recommend" not in generated_copy
