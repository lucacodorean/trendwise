from datetime import date, datetime, time, timedelta
from math import isfinite, sqrt
from statistics import fmean, pstdev
from typing import Optional, Union
from zoneinfo import ZoneInfo

from app.forecasts.models import (
    ForecastCandlestick,
    ForecastGenerationResult,
    ForecastHorizon,
    ForecastInput,
    ForecastLinePoint,
    ForecastPrediction,
    KeyFactorInput,
)


HORIZON_STEPS: dict[ForecastHorizon, tuple[int, timedelta]] = {
    ForecastHorizon.thirty_minutes: (6, timedelta(minutes=5)),
    ForecastHorizon.one_day: (8, timedelta(hours=3)),
    ForecastHorizon.five_days: (5, timedelta(days=1)),
    ForecastHorizon.seven_days: (7, timedelta(days=1)),
    ForecastHorizon.one_month: (10, timedelta(days=3)),
    ForecastHorizon.six_months: (12, timedelta(days=15)),
    ForecastHorizon.one_year: (12, timedelta(days=30)),
}

SIGNAL_SCALE: dict[ForecastHorizon, float] = {
    ForecastHorizon.thirty_minutes: 0.08,
    ForecastHorizon.one_day: 0.25,
    ForecastHorizon.five_days: 1.0,
    ForecastHorizon.seven_days: 1.0,
    ForecastHorizon.one_month: 2.0,
    ForecastHorizon.six_months: 5.0,
    ForecastHorizon.one_year: 8.0,
}

VOLATILITY_SCALE: dict[ForecastHorizon, float] = {
    ForecastHorizon.thirty_minutes: 0.25,
    ForecastHorizon.one_day: 0.5,
    ForecastHorizon.five_days: 1.0,
    ForecastHorizon.seven_days: 1.15,
    ForecastHorizon.one_month: 1.8,
    ForecastHorizon.six_months: 3.5,
    ForecastHorizon.one_year: 5.0,
}

MARKET_TIME_ZONE = ZoneInfo("America/New_York")
LOCAL_REGULAR_MARKET_OPEN = time(hour=9, minute=30)
LOCAL_REGULAR_MARKET_CLOSE = time(hour=16, minute=0)
INTRADAY_HORIZONS = {ForecastHorizon.thirty_minutes, ForecastHorizon.one_day}
EXTERNAL_FACTOR_WEIGHT_SCALE: dict[ForecastHorizon, float] = {
    ForecastHorizon.thirty_minutes: 1.25,
    ForecastHorizon.one_day: 1.15,
    ForecastHorizon.five_days: 1.0,
    ForecastHorizon.seven_days: 0.95,
    ForecastHorizon.one_month: 0.85,
    ForecastHorizon.six_months: 0.7,
    ForecastHorizon.one_year: 0.6,
}


class ForecastInputError(ValueError):
    pass


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def normalize_horizon(horizon: Union[ForecastHorizon, str]) -> ForecastHorizon:
    if isinstance(horizon, ForecastHorizon):
        return horizon
    try:
        return ForecastHorizon(horizon)
    except ValueError as error:
        raise ForecastInputError(f"Unsupported forecast horizon: {horizon}") from error


def validate_input(forecast_input: ForecastInput, *, now: Optional[datetime] = None, max_market_snapshot_age: Optional[timedelta] = None) -> ForecastHorizon:
    horizon = normalize_horizon(forecast_input.horizon)
    if not isfinite(forecast_input.market_snapshot.latest_price):
        raise ForecastInputError("Latest observed price must be finite")
    if forecast_input.market_snapshot.latest_price <= 0:
        raise ForecastInputError("Latest observed price must be positive")
    observed_at = forecast_input.market_snapshot.observed_at
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ForecastInputError("Market snapshot observed_at must be timezone-aware")
    if now is not None and max_market_snapshot_age is not None:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ForecastInputError("Staleness check now must be timezone-aware")
        if now - observed_at > max_market_snapshot_age:
            raise ForecastInputError("Market snapshot is stale")
    for point in forecast_input.historical_prices:
        if not isfinite(point.close):
            raise ForecastInputError("Historical close prices must be finite")
        if point.close <= 0:
            raise ForecastInputError("Historical close prices must be positive")
    return horizon


def close_to_close_returns(forecast_input: ForecastInput) -> list[float]:
    prices = sorted(forecast_input.historical_prices, key=lambda point: point.timestamp)
    returns: list[float] = []
    for previous, current in zip(prices, prices[1:]):
        returns.append((current.close - previous.close) / previous.close)
    return returns


def market_open_at(value: datetime) -> datetime:
    local_value = value.astimezone(MARKET_TIME_ZONE)
    local_open = local_value.replace(
        hour=LOCAL_REGULAR_MARKET_OPEN.hour,
        minute=LOCAL_REGULAR_MARKET_OPEN.minute,
        second=0,
        microsecond=0,
    )
    return local_open.astimezone(value.tzinfo)


def market_close_at(value: datetime) -> datetime:
    local_value = value.astimezone(MARKET_TIME_ZONE)
    local_close = local_value.replace(
        hour=LOCAL_REGULAR_MARKET_CLOSE.hour,
        minute=LOCAL_REGULAR_MARKET_CLOSE.minute,
        second=0,
        microsecond=0,
    )
    return local_close.astimezone(value.tzinfo)


def market_open_on(local_date: date, tzinfo) -> datetime:
    return datetime.combine(local_date, LOCAL_REGULAR_MARKET_OPEN, tzinfo=MARKET_TIME_ZONE).astimezone(tzinfo)


def next_trading_day_open(value: datetime) -> datetime:
    candidate_date = value.astimezone(MARKET_TIME_ZONE).date() + timedelta(days=1)
    while not is_trading_session(candidate_date):
        candidate_date += timedelta(days=1)
    return market_open_on(candidate_date, value.tzinfo)


def normalize_to_trading_session(value: datetime) -> datetime:
    local_candidate = value.astimezone(MARKET_TIME_ZONE)
    while not is_trading_session(local_candidate.date()):
        local_candidate = datetime.combine(
            local_candidate.date() + timedelta(days=1),
            LOCAL_REGULAR_MARKET_OPEN,
            tzinfo=MARKET_TIME_ZONE,
        )

    if local_candidate.time() < LOCAL_REGULAR_MARKET_OPEN:
        return market_open_on(local_candidate.date(), value.tzinfo)
    if local_candidate.time() > LOCAL_REGULAR_MARKET_CLOSE:
        return next_trading_day_open(local_candidate.astimezone(value.tzinfo))
    return local_candidate.astimezone(value.tzinfo)


def add_regular_market_time(value: datetime, interval: timedelta) -> datetime:
    current = normalize_to_trading_session(value)
    remaining = interval
    while remaining > timedelta(0):
        close_at = market_close_at(current)
        available = close_at - current
        if remaining <= available:
            return current + remaining
        remaining -= available
        current = next_trading_day_open(current)
    return current


def add_trading_session_interval(value: datetime, interval: timedelta) -> datetime:
    local_target = value.astimezone(MARKET_TIME_ZONE) + interval
    return normalize_to_trading_session(local_target.astimezone(value.tzinfo))


def observed_fixed_holiday(year: int, month: int, day: int) -> date:
    holiday = date(year, month, day)
    if holiday.weekday() == 5:
        return holiday - timedelta(days=1)
    if holiday.weekday() == 6:
        return holiday + timedelta(days=1)
    return holiday


def nth_weekday(year: int, month: int, weekday: int, occurrence: int) -> date:
    candidate = date(year, month, 1)
    while candidate.weekday() != weekday:
        candidate += timedelta(days=1)
    return candidate + timedelta(days=7 * (occurrence - 1))


def last_weekday(year: int, month: int, weekday: int) -> date:
    candidate = date(year, month + 1, 1) - timedelta(days=1)
    while candidate.weekday() != weekday:
        candidate -= timedelta(days=1)
    return candidate


def easter_date(year: int) -> date:
    century_remainder = year % 19
    century = year // 100
    leap_years_skipped = century // 4
    correction = (century + 8) // 25
    moon_correction = (century - correction + 1) // 3
    epact = (19 * century_remainder + century - leap_years_skipped - moon_correction + 15) % 30
    year_remainder = year % 100
    leap_remainder = year_remainder // 4
    weekday_correction = (32 + 2 * (century % 4) + 2 * leap_remainder - epact - (year_remainder % 4)) % 7
    month_offset = (century_remainder + 11 * epact + 22 * weekday_correction) // 451
    month = (epact + weekday_correction - 7 * month_offset + 114) // 31
    day = ((epact + weekday_correction - 7 * month_offset + 114) % 31) + 1
    return date(year, month, day)


def market_holidays(year: int) -> set[date]:
    return {
        observed_fixed_holiday(year, 1, 1),
        nth_weekday(year, 1, 0, 3),
        nth_weekday(year, 2, 0, 3),
        easter_date(year) - timedelta(days=2),
        last_weekday(year, 5, 0),
        observed_fixed_holiday(year, 6, 19),
        observed_fixed_holiday(year, 7, 4),
        nth_weekday(year, 9, 0, 1),
        nth_weekday(year, 11, 3, 4),
        observed_fixed_holiday(year, 12, 25),
    }


def is_trading_session(value: date) -> bool:
    return (
        value.weekday() < 5
        and value not in market_holidays(value.year)
        and value not in market_holidays(value.year + 1)
    )


def generate_forecast_timestamps(generated_at: datetime, horizon: ForecastHorizon, count: int, interval: timedelta) -> list[datetime]:
    timestamps: list[datetime] = []
    current = generated_at
    for _sequence in range(count):
        if horizon in INTRADAY_HORIZONS:
            current = add_regular_market_time(current, interval)
        else:
            current = add_trading_session_interval(current, interval)
        timestamps.append(current)
    return timestamps


def derive_signal_and_volatility(returns: list[float]) -> tuple[float, float, bool]:
    if len(returns) < 2:
        return 0.0, 0.04, True

    recent_returns = returns[-5:]
    signal = clamp(fmean(recent_returns), -0.03, 0.03)
    volatility = max(pstdev(recent_returns), 0.005)
    return signal, volatility, False


def generate_line_points(forecast_input: ForecastInput, horizon: ForecastHorizon, signal: float, volatility: float, neutral_fallback: bool) -> list[ForecastLinePoint]:
    count, interval = HORIZON_STEPS[horizon]
    latest_price = forecast_input.market_snapshot.latest_price
    generated_at = forecast_input.market_snapshot.observed_at
    timestamps = generate_forecast_timestamps(generated_at, horizon, count, interval)
    step_signal = signal * SIGNAL_SCALE[horizon]
    volatility_scale = VOLATILITY_SCALE[horizon] * (1.5 if neutral_fallback else 1.0)
    minimum_uncertainty = 0.02 if neutral_fallback else 0.005

    line_points: list[ForecastLinePoint] = []
    for sequence, timestamp in enumerate(timestamps, start=1):
        expected_value = max(latest_price * ((1 + step_signal) ** sequence), 0.01)
        uncertainty_percent = max(volatility * volatility_scale * sqrt(sequence), minimum_uncertainty)
        uncertainty = expected_value * uncertainty_percent
        line_points.append(
            ForecastLinePoint(
                sequence=sequence,
                timestamp=timestamp,
                expected_value=round(expected_value, 4),
                lower_bound=round(max(expected_value - uncertainty, 0.01), 4),
                upper_bound=round(expected_value + uncertainty, 4),
            )
        )
    return line_points


def derive_candlesticks(forecast_input: ForecastInput, line_points: list[ForecastLinePoint]) -> list[ForecastCandlestick]:
    previous_close = forecast_input.market_snapshot.latest_price
    candlesticks: list[ForecastCandlestick] = []

    for point in line_points:
        uncertainty = max(point.expected_value - point.lower_bound, point.upper_bound - point.expected_value)
        high = max(previous_close, point.expected_value) + uncertainty
        low = max(min(previous_close, point.expected_value) - uncertainty, 0.01)
        candlesticks.append(
            ForecastCandlestick(
                sequence=point.sequence,
                timestamp=point.timestamp,
                open=previous_close,
                high=round(high, 4),
                low=round(low, 4),
                close=point.expected_value,
            )
        )
        previous_close = point.expected_value

    return candlesticks


def derive_prediction(forecast_input: ForecastInput, line_points: list[ForecastLinePoint], volatility: float, neutral_fallback: bool) -> ForecastPrediction:
    latest_price = forecast_input.market_snapshot.latest_price
    final_expected = line_points[-1].expected_value
    expected_change_percent = ((final_expected - latest_price) / latest_price) * 100

    if neutral_fallback or abs(expected_change_percent) < 0.5:
        direction = "neutral"
    elif expected_change_percent > 0:
        direction = "bullish"
    else:
        direction = "bearish"

    if neutral_fallback:
        confidence = 0.35
    else:
        confidence = clamp(0.45 + (abs(expected_change_percent) / 20) - (volatility * 4), 0.2, 0.75)

    if neutral_fallback or volatility >= 0.03:
        risk_level = "high"
    elif volatility >= 0.015:
        risk_level = "medium"
    else:
        risk_level = "low"

    return ForecastPrediction(
        direction=direction,
        confidence=round(confidence, 4),
        expected_change_percent=round(expected_change_percent, 4),
        risk_level=risk_level,
    )


def derive_key_factors(forecast_input: ForecastInput, horizon: ForecastHorizon, signal: float, volatility: float, neutral_fallback: bool) -> list[KeyFactorInput]:
    freshness_minutes = 0.0
    observed_at = forecast_input.market_snapshot.observed_at
    latest_history = max((point.timestamp for point in forecast_input.historical_prices), default=observed_at)
    if latest_history.tzinfo is not None and latest_history.utcoffset() is not None:
        freshness_minutes = max((observed_at - latest_history).total_seconds() / 60, 0.0)

    momentum_polarity = "neutral"
    if signal > 0.001:
        momentum_polarity = "positive"
    elif signal < -0.001:
        momentum_polarity = "negative"

    return [
        KeyFactorInput(
            factor_type="momentum",
            source_reference_type="historical_prices",
            source_id=None,
            label="Recent price momentum",
            value=round(signal * 100, 4),
            rationale="Close-to-close returns are used as a directional signal." if not neutral_fallback else "Recent history is limited, so directional signal remains neutral.",
            polarity=momentum_polarity,
            weight=0.3,
        ),
        KeyFactorInput(
            factor_type="volatility",
            source_reference_type="historical_prices",
            source_id=None,
            label="Historical price variability",
            value=round(volatility * 100, 4),
            rationale="Close-to-close volatility sets the forecast uncertainty range.",
            polarity="negative" if volatility >= 0.03 else "neutral",
            weight=0.25,
        ),
        KeyFactorInput(
            factor_type="freshness",
            source_reference_type="market_snapshot",
            source_id=forecast_input.market_snapshot.source_id,
            label="Market snapshot freshness",
            value=round(freshness_minutes, 4),
            rationale="The latest observed price anchors the forecast path.",
            polarity="neutral",
            weight=0.2,
        ),
        KeyFactorInput(
            factor_type="news_availability",
            source_reference_type="company_news",
            source_id=forecast_input.company_news[0].source_id if forecast_input.company_news else None,
            label="Company news availability",
            value=float(len(forecast_input.company_news)),
            rationale="Company news count is reported as context only; no sentiment is inferred.",
            polarity="neutral",
            weight=0.15,
        ),
        KeyFactorInput(
            factor_type="external_factor_availability",
            source_reference_type="external_factors",
            source_id=forecast_input.external_factors[0].source_id if forecast_input.external_factors else None,
            label="External factor availability",
            value=float(len(forecast_input.external_factors)),
            rationale="External factor count is reported as context only; no directional effect is inferred.",
            polarity="neutral",
            weight=round(0.1 * EXTERNAL_FACTOR_WEIGHT_SCALE[horizon], 4),
        ),
    ]


def generate_baseline_forecast(forecast_input: ForecastInput, *, now: Optional[datetime] = None, max_market_snapshot_age: Optional[timedelta] = None) -> ForecastGenerationResult:
    horizon = validate_input(forecast_input, now=now, max_market_snapshot_age=max_market_snapshot_age)
    returns = close_to_close_returns(forecast_input)
    signal, volatility, neutral_fallback = derive_signal_and_volatility(returns)
    line_points = generate_line_points(forecast_input, horizon, signal, volatility, neutral_fallback)
    candlesticks = derive_candlesticks(forecast_input, line_points)
    prediction = derive_prediction(forecast_input, line_points, volatility, neutral_fallback)
    key_factors = derive_key_factors(forecast_input, horizon, signal, volatility, neutral_fallback)

    return ForecastGenerationResult(
        stock=forecast_input.stock,
        horizon=horizon,
        generated_at=forecast_input.market_snapshot.observed_at,
        line_points=line_points,
        candlesticks=candlesticks,
        prediction=prediction,
        key_factors=key_factors,
    )
