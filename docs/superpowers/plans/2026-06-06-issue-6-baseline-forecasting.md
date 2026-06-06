# Issue 6 Baseline Forecasting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, ML-compatible backend pipeline that generates baseline Stock Forecasts, Candlestick Forecasts, Stock Predictions, and structured Key Factor inputs for every canonical Forecast Horizon.

**Architecture:** Add a focused `backend/app/forecasts/` module for model-compatible forecast generation and derived outputs. Keep provider/repository concerns outside the model by passing a single observed-data input object into the pipeline, then persist generated output through repository methods and expose it through the existing Stock Detail endpoint.

**Tech Stack:** Python 3.9, FastAPI, Pydantic, psycopg, Alembic, pytest, Expo-generated TypeScript OpenAPI client.

---

## Files And Responsibilities

- Create `backend/app/forecasts/__init__.py`: package marker and public exports only if needed.
- Create `backend/app/forecasts/models.py`: dataclasses/enums for `ForecastInput`, forecast points, candles, predictions, and key factor inputs.
- Create `backend/app/forecasts/baseline.py`: deterministic baseline forecast model plus line/candlestick/prediction/key-factor derivation.
- Create `backend/tests/forecasts/test_baseline.py`: unit tests for all horizons, output shapes, bounds, candle derivation, prediction derivation, key factors, no recommendation language, and no prior-prediction input.
- Modify `backend/migrations/versions/0001_initial_persistence_schema.py`: add detailed forecast output and prediction key factor tables to the current initial schema.
- Modify `backend/tests/storage/test_migrations.py`: assert the new tables, constraints, and source-link audit boundaries exist.
- Modify `backend/app/storage/repositories.py`: add repository types and persistence method for detailed forecast/prediction outputs in one transaction.
- Modify `backend/tests/storage/test_repositories.py`: assert inserts for line points, candlesticks, source links, prediction runs, and key factors; assert rollback on any failure.
- Modify `backend/app/stocks/repository.py`: load latest forecast details, candlesticks, prediction, and key factors for Stock Detail.
- Modify `backend/app/stocks/schemas.py`: add response schemas for line forecast points, candlestick forecast points, and structured key factor inputs.
- Modify `backend/app/stocks/router.py`: map repository rows into the expanded Stock Detail response.
- Modify `backend/tests/stocks/test_stock_detail.py`: cover expanded response, nullable/unavailable sections, repository queries, and recommendation-language absence.
- Modify `backend/app/database/seeders/stock_detail.py`: seed deterministic detail rows for the local prototype Stock Detail endpoint.
- Modify `backend/app/database/seed_data/stock_detail.csv`: add compact JSON columns for generated line points, candlesticks, and key factor inputs.
- Regenerate `mobile/src/api/generated/openapi.json` and generated TypeScript models/services after backend schema changes.

## Domain Decisions For This Slice

- Forecast generation accepts observed source data only: stock identity, horizon, latest market snapshot, historical prices, company news, and external factors.
- Forecast generation does not accept or read prior Stock Predictions.
- The baseline model is deterministic and intentionally conservative; it is shaped so a trained model can later replace the implementation behind the same input/output objects.
- History with fewer than two valid close prices but a valid latest price produces a neutral forecast with wider uncertainty and lower confidence.
- Missing or malformed required market data fails before computed outputs are persisted.
- Missing optional Company News or External Factors does not block generation; key factor inputs should state absence/count/freshness without inventing sentiment.
- Do not add polished prose, LLM summaries, buy/sell/hold labels, or recommendation framing.

---

### Task 1: Forecast Domain Models

**Files:**
- Create: `backend/app/forecasts/__init__.py`
- Create: `backend/app/forecasts/models.py`
- Test: `backend/tests/forecasts/test_baseline.py`

- [ ] **Step 1: Write the failing model-shape tests**

Add `backend/tests/forecasts/test_baseline.py` with the initial tests below:

```python
from datetime import datetime, timedelta, timezone

from app.forecasts.baseline import generate_baseline_forecast
from app.forecasts.models import (
    CompanyNewsSignal,
    ExternalFactorSignal,
    ForecastInput,
    HistoricalPricePoint,
    MarketSnapshotInput,
    StockIdentity,
)


def build_input(horizon: str = "1d") -> ForecastInput:
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


def test_generate_baseline_forecast_returns_model_compatible_output() -> None:
    result = generate_baseline_forecast(build_input())

    assert result.horizon == "1d"
    assert result.generated_at == datetime(2026, 6, 6, 14, 30, tzinfo=timezone.utc)
    assert len(result.line_points) > 0
    assert len(result.candlesticks) == len(result.line_points)
    assert result.prediction.direction in {"bullish", "bearish", "neutral"}
    assert 0 <= result.prediction.confidence <= 1
    assert result.prediction.risk_level in {"low", "medium", "high"}
    assert result.key_factors
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `cd backend && pytest tests/forecasts/test_baseline.py -v`

Expected: FAIL because `app.forecasts` does not exist.

- [ ] **Step 3: Create the forecast package and models**

Create `backend/app/forecasts/__init__.py`:

```python
"""Forecast generation components."""
```

Create `backend/app/forecasts/models.py`:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional


ForecastDirection = Literal["bullish", "bearish", "neutral"]
RiskLevel = Literal["low", "medium", "high"]
KeyFactorPolarity = Literal["positive", "negative", "neutral"]


@dataclass(frozen=True)
class StockIdentity:
    ticker: str
    company_name: str
    exchange: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ticker", self.ticker.strip().upper())
        object.__setattr__(self, "company_name", self.company_name.strip())
        object.__setattr__(self, "exchange", self.exchange.strip())


@dataclass(frozen=True)
class MarketSnapshotInput:
    latest_price: float
    daily_change: Optional[float]
    daily_change_percent: Optional[float]
    observed_at: datetime
    source_id: Optional[int] = None


@dataclass(frozen=True)
class HistoricalPricePoint:
    timestamp: datetime
    close: float


@dataclass(frozen=True)
class CompanyNewsSignal:
    source_id: Optional[int]
    title: str
    published_at: datetime


@dataclass(frozen=True)
class ExternalFactorSignal:
    source_id: Optional[int]
    factor_type: str
    label: str
    observed_at: datetime


@dataclass(frozen=True)
class ForecastInput:
    stock: StockIdentity
    horizon: str
    market_snapshot: MarketSnapshotInput
    historical_prices: list[HistoricalPricePoint]
    company_news: list[CompanyNewsSignal]
    external_factors: list[ExternalFactorSignal]


@dataclass(frozen=True)
class ForecastLinePoint:
    sequence: int
    timestamp: datetime
    expected_value: float
    lower_bound: float
    upper_bound: float


@dataclass(frozen=True)
class ForecastCandlestick:
    sequence: int
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class ForecastPrediction:
    direction: ForecastDirection
    confidence: float
    expected_change_percent: float
    risk_level: RiskLevel


@dataclass(frozen=True)
class KeyFactorInput:
    factor_type: str
    source_reference_type: Optional[str]
    source_id: Optional[int]
    label: str
    value: Optional[float]
    rationale: Optional[str]
    polarity: KeyFactorPolarity
    weight: Optional[float]


@dataclass(frozen=True)
class ForecastGenerationResult:
    stock: StockIdentity
    horizon: str
    generated_at: datetime
    line_points: list[ForecastLinePoint]
    candlesticks: list[ForecastCandlestick]
    prediction: ForecastPrediction
    key_factors: list[KeyFactorInput]
```

- [ ] **Step 4: Add a minimal baseline module**

Create `backend/app/forecasts/baseline.py`:

```python
from app.forecasts.models import ForecastGenerationResult, ForecastInput


def generate_baseline_forecast(forecast_input: ForecastInput) -> ForecastGenerationResult:
    raise NotImplementedError("Baseline forecast generation is implemented in Task 2")
```

- [ ] **Step 5: Run the focused tests**

Run: `cd backend && pytest tests/forecasts/test_baseline.py -v`

Expected: one import/model test passes and generation test fails with `NotImplementedError`.

- [ ] **Step 6: Commit**

Run: `git add backend/app/forecasts backend/tests/forecasts/test_baseline.py && git commit -m "feat: add forecast domain models"`

---

### Task 2: Deterministic Baseline Forecast Generation

**Files:**
- Modify: `backend/app/forecasts/baseline.py`
- Modify: `backend/tests/forecasts/test_baseline.py`

- [ ] **Step 1: Add tests for all horizons, point bounds, neutral fallback, and recommendation-language absence**

Append to `backend/tests/forecasts/test_baseline.py`:

```python
import pytest


@pytest.mark.parametrize(
    ("horizon", "expected_count"),
    [
        ("30m", 6),
        ("1d", 8),
        ("5d", 5),
        ("7d", 7),
        ("1mo", 10),
        ("6mo", 12),
        ("1y", 12),
    ],
)
def test_all_canonical_horizons_generate_valid_line_points(horizon: str, expected_count: int) -> None:
    result = generate_baseline_forecast(build_input(horizon))

    assert len(result.line_points) == expected_count
    for index, point in enumerate(result.line_points, start=1):
        assert point.sequence == index
        assert point.timestamp > result.generated_at
        assert point.lower_bound <= point.expected_value <= point.upper_bound


def test_candlesticks_are_derived_from_expected_path_and_uncertainty() -> None:
    result = generate_baseline_forecast(build_input("1d"))
    latest_price = result.line_points[0].expected_value

    first_candle = result.candlesticks[0]
    assert first_candle.open == latest_price
    assert first_candle.close == result.line_points[0].expected_value
    assert first_candle.high >= max(first_candle.open, first_candle.close)
    assert first_candle.low <= min(first_candle.open, first_candle.close)

    second_candle = result.candlesticks[1]
    assert second_candle.open == result.line_points[0].expected_value
    assert second_candle.close == result.line_points[1].expected_value


def test_short_history_generates_neutral_wider_uncertainty_forecast() -> None:
    source = build_input("1d")
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


def test_generated_labels_do_not_use_recommendation_language() -> None:
    result = generate_baseline_forecast(build_input())
    labels = " ".join(factor.label for factor in result.key_factors).lower()
    rationales = " ".join(factor.rationale or "" for factor in result.key_factors).lower()
    generated_copy = f"{labels} {rationales}"

    assert "buy" not in generated_copy
    assert "sell" not in generated_copy
    assert "hold" not in generated_copy
    assert "recommend" not in generated_copy
```

- [ ] **Step 2: Run the focused tests to verify failure**

Run: `cd backend && pytest tests/forecasts/test_baseline.py -v`

Expected: FAIL because `generate_baseline_forecast` still raises `NotImplementedError`.

- [ ] **Step 3: Implement deterministic baseline generation**

Replace `backend/app/forecasts/baseline.py` with:

```python
from datetime import timedelta
from math import sqrt
from statistics import mean, stdev

from app.forecasts.models import (
    ForecastCandlestick,
    ForecastGenerationResult,
    ForecastInput,
    ForecastLinePoint,
    ForecastPrediction,
    KeyFactorInput,
)


HORIZON_STEPS: dict[str, tuple[int, timedelta]] = {
    "30m": (6, timedelta(minutes=5)),
    "1d": (8, timedelta(hours=3)),
    "5d": (5, timedelta(days=1)),
    "7d": (7, timedelta(days=1)),
    "1mo": (10, timedelta(days=3)),
    "6mo": (12, timedelta(days=15)),
    "1y": (12, timedelta(days=30)),
}


class ForecastInputError(ValueError):
    pass


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def validate_input(forecast_input: ForecastInput) -> None:
    if forecast_input.horizon not in HORIZON_STEPS:
        raise ForecastInputError(f"Unsupported Forecast Horizon: {forecast_input.horizon}")
    if forecast_input.market_snapshot.latest_price <= 0:
        raise ForecastInputError("Latest Market Snapshot price must be positive")
    if forecast_input.market_snapshot.observed_at.tzinfo is None:
        raise ForecastInputError("Market Snapshot observed_at must be timezone-aware")


def close_to_close_returns(closes: list[float]) -> list[float]:
    returns: list[float] = []
    for previous, current in zip(closes, closes[1:]):
        if previous > 0:
            returns.append((current - previous) / previous)
    return returns


def derive_signal_and_volatility(forecast_input: ForecastInput) -> tuple[float, float, bool]:
    closes = [point.close for point in forecast_input.historical_prices if point.close > 0]
    returns = close_to_close_returns(closes)
    if len(returns) < 2:
        return 0.0, 0.035, True
    recent_signal = mean(returns[-3:])
    volatility = stdev(returns) if len(returns) > 1 else abs(recent_signal)
    return clamp(recent_signal, -0.03, 0.03), clamp(volatility, 0.005, 0.08), False


def generate_line_points(forecast_input: ForecastInput) -> list[ForecastLinePoint]:
    step_count, step_delta = HORIZON_STEPS[forecast_input.horizon]
    latest_price = forecast_input.market_snapshot.latest_price
    signal, volatility, short_history = derive_signal_and_volatility(forecast_input)
    uncertainty_multiplier = 2.4 if short_history else 1.6
    points: list[ForecastLinePoint] = []
    for sequence in range(1, step_count + 1):
        expected_value = latest_price * (1 + signal * sequence)
        scaled_uncertainty = latest_price * volatility * sqrt(sequence) * uncertainty_multiplier
        points.append(
            ForecastLinePoint(
                sequence=sequence,
                timestamp=forecast_input.market_snapshot.observed_at + step_delta * sequence,
                expected_value=round(expected_value, 4),
                lower_bound=round(max(0.01, expected_value - scaled_uncertainty), 4),
                upper_bound=round(expected_value + scaled_uncertainty, 4),
            )
        )
    return points


def derive_candlesticks(latest_price: float, line_points: list[ForecastLinePoint]) -> list[ForecastCandlestick]:
    candles: list[ForecastCandlestick] = []
    previous_expected = latest_price
    for point in line_points:
        range_padding = max(point.expected_value - point.lower_bound, point.upper_bound - point.expected_value) * 0.35
        high = max(previous_expected, point.expected_value) + range_padding
        low = min(previous_expected, point.expected_value) - range_padding
        candles.append(
            ForecastCandlestick(
                sequence=point.sequence,
                timestamp=point.timestamp,
                open=round(previous_expected, 4),
                high=round(high, 4),
                low=round(max(0.01, low), 4),
                close=point.expected_value,
            )
        )
        previous_expected = point.expected_value
    return candles


def derive_prediction(latest_price: float, line_points: list[ForecastLinePoint], short_history: bool) -> ForecastPrediction:
    final_point = line_points[-1]
    expected_change_percent = ((final_point.expected_value - latest_price) / latest_price) * 100
    final_range_percent = ((final_point.upper_bound - final_point.lower_bound) / latest_price) * 100
    signal_to_uncertainty = abs(expected_change_percent) / max(final_range_percent, 0.01)
    if abs(expected_change_percent) < 0.25 or short_history:
        direction = "neutral"
    elif expected_change_percent > 0:
        direction = "bullish"
    else:
        direction = "bearish"
    confidence = 0.3 if short_history else clamp(0.45 + signal_to_uncertainty * 0.35, 0.35, 0.85)
    if final_range_percent >= 12 or short_history:
        risk_level = "high"
    elif final_range_percent >= 5:
        risk_level = "medium"
    else:
        risk_level = "low"
    return ForecastPrediction(
        direction=direction,
        confidence=round(confidence, 4),
        expected_change_percent=round(expected_change_percent, 4),
        risk_level=risk_level,
    )


def derive_key_factors(forecast_input: ForecastInput, prediction: ForecastPrediction, short_history: bool) -> list[KeyFactorInput]:
    market = forecast_input.market_snapshot
    news_count = len(forecast_input.company_news)
    external_count = len(forecast_input.external_factors)
    factors = [
        KeyFactorInput(
            factor_type="momentum",
            source_reference_type="market_snapshot",
            source_id=market.source_id,
            label="Recent price momentum",
            value=prediction.expected_change_percent,
            rationale="Baseline direction is derived from recent close-to-close movement.",
            polarity="positive" if prediction.expected_change_percent > 0 else "negative" if prediction.expected_change_percent < 0 else "neutral",
            weight=0.45,
        ),
        KeyFactorInput(
            factor_type="volatility",
            source_reference_type="historical_prices",
            source_id=None,
            label="Historical volatility range",
            value=None,
            rationale="Forecast bounds widen when recent price movement is more variable.",
            polarity="neutral",
            weight=0.3,
        ),
        KeyFactorInput(
            factor_type="freshness",
            source_reference_type="market_snapshot",
            source_id=market.source_id,
            label="Market data freshness",
            value=None,
            rationale=f"Latest observed Market Snapshot at {market.observed_at.isoformat()}.",
            polarity="neutral",
            weight=0.15,
        ),
        KeyFactorInput(
            factor_type="news",
            source_reference_type="company_news",
            source_id=None,
            label="Company news availability",
            value=float(news_count),
            rationale=f"{news_count} Company News item(s) available; no sentiment is inferred.",
            polarity="neutral",
            weight=0.05,
        ),
        KeyFactorInput(
            factor_type="external_factor",
            source_reference_type="external_factor",
            source_id=None,
            label="External factor availability",
            value=float(external_count),
            rationale=f"{external_count} External Factor input(s) available for audit linkage.",
            polarity="neutral",
            weight=0.05,
        ),
    ]
    if short_history:
        factors.append(
            KeyFactorInput(
                factor_type="volatility",
                source_reference_type="historical_prices",
                source_id=None,
                label="Limited historical price context",
                value=None,
                rationale="Short history uses a neutral baseline with wider uncertainty.",
                polarity="neutral",
                weight=0.2,
            )
        )
    return factors


def generate_baseline_forecast(forecast_input: ForecastInput) -> ForecastGenerationResult:
    validate_input(forecast_input)
    _, _, short_history = derive_signal_and_volatility(forecast_input)
    line_points = generate_line_points(forecast_input)
    candlesticks = derive_candlesticks(forecast_input.market_snapshot.latest_price, line_points)
    prediction = derive_prediction(forecast_input.market_snapshot.latest_price, line_points, short_history)
    return ForecastGenerationResult(
        stock=forecast_input.stock,
        horizon=forecast_input.horizon,
        generated_at=forecast_input.market_snapshot.observed_at,
        line_points=line_points,
        candlesticks=candlesticks,
        prediction=prediction,
        key_factors=derive_key_factors(forecast_input, prediction, short_history),
    )
```

- [ ] **Step 4: Run forecast tests**

Run: `cd backend && pytest tests/forecasts/test_baseline.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add backend/app/forecasts/baseline.py backend/tests/forecasts/test_baseline.py && git commit -m "feat: generate baseline stock forecasts"`

---

### Task 3: Detailed Persistence Schema

**Files:**
- Modify: `backend/migrations/versions/0001_initial_persistence_schema.py`
- Modify: `backend/tests/storage/test_migrations.py`

- [ ] **Step 1: Add failing migration tests for detail tables**

Append to `backend/tests/storage/test_migrations.py`:

```python

def test_initial_migration_defines_forecast_output_detail_tables() -> None:
    migration = migration_path().read_text()

    for table_name in (
        "forecast_line_points",
        "forecast_candlesticks",
        "prediction_key_factors",
    ):
        assert_create_table_call_exists(migration, table_name)

    line_start = create_table_start(migration, "forecast_line_points")
    candles_start = create_table_start(migration, "forecast_candlesticks")
    factors_start = create_table_start(migration, "prediction_key_factors")
    line_section = migration[line_start:candles_start]
    candle_section = migration[candles_start:factors_start]
    factor_section = migration[factors_start:]

    assert "forecast_runs.id" in line_section
    assert "expected_value" in line_section
    assert "lower_bound" in line_section
    assert "upper_bound" in line_section
    assert "uq_forecast_line_points_run_sequence" in line_section
    assert "forecast_runs.id" in candle_section
    assert "open_price" in candle_section
    assert "high_price" in candle_section
    assert "low_price" in candle_section
    assert "close_price" in candle_section
    assert "uq_forecast_candlesticks_run_sequence" in candle_section
    assert "prediction_runs.id" in factor_section
    assert "factor_type" in factor_section
    assert "source_reference_type" in factor_section
    assert "source_id" in factor_section
    assert "polarity" in factor_section
```

- [ ] **Step 2: Run migration tests to verify failure**

Run: `cd backend && pytest tests/storage/test_migrations.py -v`

Expected: FAIL because the detail tables do not exist.

- [ ] **Step 3: Add detail tables in the migration**

In `backend/migrations/versions/0001_initial_persistence_schema.py`, add these `op.create_table` calls after `forecast_source_external_factors` and before `job_statuses`:

```python
    op.create_table(
        "forecast_line_points",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("forecast_run_id", sa.BigInteger(), sa.ForeignKey("forecast_runs.id"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_value", sa.Numeric(), nullable=False),
        sa.Column("lower_bound", sa.Numeric(), nullable=False),
        sa.Column("upper_bound", sa.Numeric(), nullable=False),
        sa.UniqueConstraint("forecast_run_id", "sequence", name="uq_forecast_line_points_run_sequence"),
    )

    op.create_table(
        "forecast_candlesticks",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("forecast_run_id", sa.BigInteger(), sa.ForeignKey("forecast_runs.id"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open_price", sa.Numeric(), nullable=False),
        sa.Column("high_price", sa.Numeric(), nullable=False),
        sa.Column("low_price", sa.Numeric(), nullable=False),
        sa.Column("close_price", sa.Numeric(), nullable=False),
        sa.UniqueConstraint("forecast_run_id", "sequence", name="uq_forecast_candlesticks_run_sequence"),
    )

    op.create_table(
        "prediction_key_factors",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("prediction_run_id", sa.BigInteger(), sa.ForeignKey("prediction_runs.id"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("factor_type", sa.Text(), nullable=False),
        sa.Column("source_reference_type", sa.Text(), nullable=True),
        sa.Column("source_id", sa.BigInteger(), nullable=True),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("numeric_value", sa.Numeric(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("polarity", sa.Text(), nullable=False),
        sa.Column("weight", sa.Numeric(), nullable=True),
        sa.CheckConstraint("polarity IN ('positive', 'negative', 'neutral')", name="ck_prediction_key_factors_polarity"),
        sa.UniqueConstraint("prediction_run_id", "sequence", name="uq_prediction_key_factors_run_sequence"),
    )
```

Update `downgrade()` so the new tables are dropped before `prediction_runs` and `forecast_runs`:

```python
        "prediction_key_factors",
        "forecast_candlesticks",
        "forecast_line_points",
```

- [ ] **Step 4: Run migration tests**

Run: `cd backend && pytest tests/storage/test_migrations.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add backend/migrations/versions/0001_initial_persistence_schema.py backend/tests/storage/test_migrations.py && git commit -m "feat: add forecast output persistence schema"`

---

### Task 4: Detailed Persistence Repository

**Files:**
- Modify: `backend/app/storage/repositories.py`
- Modify: `backend/tests/storage/test_repositories.py`

- [ ] **Step 1: Add failing repository tests for detailed writes**

Append to `backend/tests/storage/test_repositories.py`:

```python
from app.forecasts.models import ForecastCandlestick, ForecastLinePoint, ForecastPrediction, KeyFactorInput


def test_repository_stores_detailed_forecast_outputs_in_one_transaction() -> None:
    connection = RecordingConnection()
    connection.cursor_instance.return_values = [(101,), (201,), (301,), (401,)]
    repository = PostgresPersistenceRepository(connection)
    generated_at = datetime(2026, 6, 6, 14, 30, tzinfo=timezone.utc)

    result = repository.store_detailed_forecast_prediction(
        ticker="aapl",
        company_name="Apple Inc.",
        exchange="NASDAQ",
        horizon="1d",
        latest_price=214.35,
        daily_change=2.62,
        daily_change_percent=1.24,
        observed_at=generated_at,
        forecast_status="available",
        forecast_generated_at=generated_at,
        line_points=[ForecastLinePoint(1, generated_at, 215.0, 210.0, 220.0)],
        candlesticks=[ForecastCandlestick(1, generated_at, 214.35, 220.0, 210.0, 215.0)],
        prediction=ForecastPrediction("bullish", 0.68, 0.3, "medium"),
        prediction_generated_at=generated_at,
        key_factors=[
            KeyFactorInput("momentum", "market_snapshot", 201, "Recent price momentum", 0.3, "Derived from observed prices.", "positive", 0.45)
        ],
        company_news_ids=[301],
        external_factor_ids=[401],
    )

    assert result == {
        "stock_id": 101,
        "market_snapshot_id": 201,
        "forecast_run_id": 301,
        "prediction_run_id": 401,
    }
    sql = "\n".join(statement for statement, _ in connection.cursor_instance.executions)
    assert "INSERT INTO forecast_line_points" in sql
    assert "INSERT INTO forecast_candlesticks" in sql
    assert "INSERT INTO forecast_source_company_news" in sql
    assert "INSERT INTO forecast_source_external_factors" in sql
    assert "INSERT INTO prediction_key_factors" in sql
    assert "prediction_runs.id" not in sql.split("INSERT INTO forecast_source_market_snapshots", 1)[1].split("INSERT INTO prediction_runs", 1)[0]
    assert connection.commits == 1
```

- [ ] **Step 2: Run repository tests to verify failure**

Run: `cd backend && pytest tests/storage/test_repositories.py -v`

Expected: FAIL because `store_detailed_forecast_prediction` does not exist.

- [ ] **Step 3: Implement detailed persistence method**

In `backend/app/storage/repositories.py`, import forecast model types:

```python
from app.forecasts.models import ForecastCandlestick, ForecastLinePoint, ForecastPrediction, KeyFactorInput
```

Add this method to `PostgresPersistenceRepository` after `store_snapshot_forecast_prediction`:

```python
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
        ids = self.store_snapshot_forecast_prediction(
            ticker=ticker,
            company_name=company_name,
            exchange=exchange,
            horizon=horizon,
            latest_price=latest_price,
            daily_change=daily_change,
            daily_change_percent=daily_change_percent,
            observed_at=observed_at,
            forecast_status=forecast_status,
            forecast_generated_at=forecast_generated_at,
            prediction_direction=prediction.direction,
            prediction_confidence=prediction.confidence,
            prediction_expected_change_percent=prediction.expected_change_percent,
            prediction_risk_level=prediction.risk_level,
            prediction_generated_at=prediction_generated_at,
        )
        try:
            with self.connection.cursor() as cursor:
                for point in line_points:
                    cursor.execute(
                        """
                        INSERT INTO forecast_line_points (
                            forecast_run_id, sequence, timestamp, expected_value, lower_bound, upper_bound
                        ) VALUES (
                            %(forecast_run_id)s, %(sequence)s, %(timestamp)s, %(expected_value)s, %(lower_bound)s, %(upper_bound)s
                        )
                        ON CONFLICT (forecast_run_id, sequence) DO UPDATE SET
                            timestamp = EXCLUDED.timestamp,
                            expected_value = EXCLUDED.expected_value,
                            lower_bound = EXCLUDED.lower_bound,
                            upper_bound = EXCLUDED.upper_bound
                        """,
                        {
                            "forecast_run_id": ids["forecast_run_id"],
                            "sequence": point.sequence,
                            "timestamp": point.timestamp,
                            "expected_value": point.expected_value,
                            "lower_bound": point.lower_bound,
                            "upper_bound": point.upper_bound,
                        },
                    )
                for candle in candlesticks:
                    cursor.execute(
                        """
                        INSERT INTO forecast_candlesticks (
                            forecast_run_id, sequence, timestamp, open_price, high_price, low_price, close_price
                        ) VALUES (
                            %(forecast_run_id)s, %(sequence)s, %(timestamp)s, %(open_price)s, %(high_price)s, %(low_price)s, %(close_price)s
                        )
                        ON CONFLICT (forecast_run_id, sequence) DO UPDATE SET
                            timestamp = EXCLUDED.timestamp,
                            open_price = EXCLUDED.open_price,
                            high_price = EXCLUDED.high_price,
                            low_price = EXCLUDED.low_price,
                            close_price = EXCLUDED.close_price
                        """,
                        {
                            "forecast_run_id": ids["forecast_run_id"],
                            "sequence": candle.sequence,
                            "timestamp": candle.timestamp,
                            "open_price": candle.open,
                            "high_price": candle.high,
                            "low_price": candle.low,
                            "close_price": candle.close,
                        },
                    )
                for company_news_id in company_news_ids:
                    cursor.execute(
                        """
                        INSERT INTO forecast_source_company_news (forecast_run_id, company_news_id)
                        VALUES (%(forecast_run_id)s, %(company_news_id)s)
                        ON CONFLICT (forecast_run_id, company_news_id) DO NOTHING
                        """,
                        {"forecast_run_id": ids["forecast_run_id"], "company_news_id": company_news_id},
                    )
                for external_factor_id in external_factor_ids:
                    cursor.execute(
                        """
                        INSERT INTO forecast_source_external_factors (forecast_run_id, external_factor_id)
                        VALUES (%(forecast_run_id)s, %(external_factor_id)s)
                        ON CONFLICT (forecast_run_id, external_factor_id) DO NOTHING
                        """,
                        {"forecast_run_id": ids["forecast_run_id"], "external_factor_id": external_factor_id},
                    )
                for sequence, factor in enumerate(key_factors, start=1):
                    cursor.execute(
                        """
                        INSERT INTO prediction_key_factors (
                            prediction_run_id, sequence, factor_type, source_reference_type, source_id,
                            label, numeric_value, rationale, polarity, weight
                        ) VALUES (
                            %(prediction_run_id)s, %(sequence)s, %(factor_type)s, %(source_reference_type)s, %(source_id)s,
                            %(label)s, %(numeric_value)s, %(rationale)s, %(polarity)s, %(weight)s
                        )
                        ON CONFLICT (prediction_run_id, sequence) DO UPDATE SET
                            factor_type = EXCLUDED.factor_type,
                            source_reference_type = EXCLUDED.source_reference_type,
                            source_id = EXCLUDED.source_id,
                            label = EXCLUDED.label,
                            numeric_value = EXCLUDED.numeric_value,
                            rationale = EXCLUDED.rationale,
                            polarity = EXCLUDED.polarity,
                            weight = EXCLUDED.weight
                        """,
                        {
                            "prediction_run_id": ids["prediction_run_id"],
                            "sequence": sequence,
                            "factor_type": factor.factor_type,
                            "source_reference_type": factor.source_reference_type,
                            "source_id": factor.source_id,
                            "label": factor.label,
                            "numeric_value": factor.value,
                            "rationale": factor.rationale,
                            "polarity": factor.polarity,
                            "weight": factor.weight,
                        },
                    )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return ids
```

- [ ] **Step 4: Run repository tests**

Run: `cd backend && pytest tests/storage/test_repositories.py -v`

Expected: PASS or expose that the helper commits before detail rows. If that happens, refactor shared stock/snapshot/run insert code into a private helper that does not commit, then keep exactly one commit at the end of `store_detailed_forecast_prediction`.

- [ ] **Step 5: Commit**

Run: `git add backend/app/storage/repositories.py backend/tests/storage/test_repositories.py && git commit -m "feat: persist detailed forecast outputs"`

---

### Task 5: Stock Detail Repository And API Schemas

**Files:**
- Modify: `backend/app/stocks/schemas.py`
- Modify: `backend/app/stocks/repository.py`
- Modify: `backend/app/stocks/router.py`
- Modify: `backend/tests/stocks/test_stock_detail.py`

- [ ] **Step 1: Add failing stock detail tests for expanded forecast and prediction payloads**

Update the `AAPL` fake detail in `backend/tests/stocks/test_stock_detail.py` so `forecast` includes `line_points` and `candlesticks`, and `prediction` includes `key_factors`:

```python
                "forecast": {
                    "id": 10,
                    "status": "available",
                    "generated_at": datetime(2026, 6, 2, 13, 15, tzinfo=timezone.utc),
                    "line_points": [
                        {
                            "sequence": 1,
                            "timestamp": datetime(2026, 6, 2, 16, 15, tzinfo=timezone.utc),
                            "expected_value": 215.0,
                            "lower_bound": 210.0,
                            "upper_bound": 220.0,
                        }
                    ],
                    "candlesticks": [
                        {
                            "sequence": 1,
                            "timestamp": datetime(2026, 6, 2, 16, 15, tzinfo=timezone.utc),
                            "open": 214.35,
                            "high": 220.0,
                            "low": 210.0,
                            "close": 215.0,
                        }
                    ],
                },
```

and:

```python
                "prediction": {
                    "direction": "bullish",
                    "confidence": 0.68,
                    "expected_change_percent": 0.8,
                    "risk_level": "medium",
                    "generated_at": datetime(2026, 6, 2, 13, 18, tzinfo=timezone.utc),
                    "key_factors": [
                        {
                            "factor_type": "momentum",
                            "source_reference_type": "market_snapshot",
                            "source_id": 201,
                            "label": "Recent price momentum",
                            "value": 0.8,
                            "rationale": "Derived from observed prices.",
                            "polarity": "positive",
                            "weight": 0.45,
                        }
                    ],
                },
```

Then update `test_stock_detail_returns_seeded_supported_stock_for_default_horizon` expected JSON forecast section to include:

```python
            "linePoints": [
                {
                    "sequence": 1,
                    "timestamp": "2026-06-02T16:15:00Z",
                    "expectedValue": 215.0,
                    "lowerBound": 210.0,
                    "upperBound": 220.0,
                }
            ],
            "candlesticks": [
                {
                    "sequence": 1,
                    "timestamp": "2026-06-02T16:15:00Z",
                    "open": 214.35,
                    "high": 220.0,
                    "low": 210.0,
                    "close": 215.0,
                }
            ],
```

and prediction section to include:

```python
            "keyFactors": [
                {
                    "factorType": "momentum",
                    "sourceReferenceType": "market_snapshot",
                    "sourceId": 201,
                    "label": "Recent price momentum",
                    "value": 0.8,
                    "rationale": "Derived from observed prices.",
                    "polarity": "positive",
                    "weight": 0.45,
                }
            ],
```

- [ ] **Step 2: Run stock detail tests to verify failure**

Run: `cd backend && pytest tests/stocks/test_stock_detail.py -v`

Expected: FAIL because the schemas do not expose detail arrays yet.

- [ ] **Step 3: Add response schemas**

In `backend/app/stocks/schemas.py`, add these models before `StockDetailForecast`:

```python
class StockDetailForecastLinePoint(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sequence: int
    timestamp: str
    expected_value: float = Field(serialization_alias="expectedValue")
    lower_bound: float = Field(serialization_alias="lowerBound")
    upper_bound: float = Field(serialization_alias="upperBound")


class StockDetailForecastCandlestick(BaseModel):
    sequence: int
    timestamp: str
    open: float
    high: float
    low: float
    close: float
```

Add this model before `StockDetailPrediction`:

```python
class StockDetailKeyFactor(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    factor_type: str = Field(serialization_alias="factorType")
    source_reference_type: Optional[str] = Field(serialization_alias="sourceReferenceType")
    source_id: Optional[int] = Field(serialization_alias="sourceId")
    label: str
    value: Optional[float]
    rationale: Optional[str]
    polarity: Literal["positive", "negative", "neutral"]
    weight: Optional[float]
```

Extend `StockDetailForecast`:

```python
    line_points: list[StockDetailForecastLinePoint] = Field(default_factory=list, serialization_alias="linePoints")
    candlesticks: list[StockDetailForecastCandlestick] = Field(default_factory=list)
```

Extend `StockDetailPrediction`:

```python
    key_factors: list[StockDetailKeyFactor] = Field(default_factory=list, serialization_alias="keyFactors")
```

- [ ] **Step 4: Map expanded data in the router**

In `backend/app/stocks/router.py`, import the new schema models and pass empty arrays for unavailable sections. For available forecast rows, map each row with `format_utc_datetime(row["timestamp"])`. For available prediction rows, map key factors directly with field names from the repository.

- [ ] **Step 5: Extend repository row types and queries**

In `backend/app/stocks/repository.py`, add typed dicts for line points, candlesticks, and key factors, then after the latest forecast query load:

```sql
SELECT sequence, timestamp, expected_value, lower_bound, upper_bound
FROM forecast_line_points
WHERE forecast_run_id = %(forecast_run_id)s
ORDER BY sequence ASC
```

and:

```sql
SELECT sequence, timestamp, open_price, high_price, low_price, close_price
FROM forecast_candlesticks
WHERE forecast_run_id = %(forecast_run_id)s
ORDER BY sequence ASC
```

After selecting the prediction row, include its id and load:

```sql
SELECT factor_type, source_reference_type, source_id, label, numeric_value, rationale, polarity, weight
FROM prediction_key_factors
WHERE prediction_run_id = %(prediction_run_id)s
ORDER BY sequence ASC
```

Convert numeric database values with `numeric_to_float` / `optional_numeric_to_float`.

- [ ] **Step 6: Run stock detail tests**

Run: `cd backend && pytest tests/stocks/test_stock_detail.py -v`

Expected: PASS after updating fake cursor rows and expected repository SQL assertions to account for the added queries.

- [ ] **Step 7: Commit**

Run: `git add backend/app/stocks/schemas.py backend/app/stocks/repository.py backend/app/stocks/router.py backend/tests/stocks/test_stock_detail.py && git commit -m "feat: expose forecast detail payloads"`

---

### Task 6: Seeded Prototype Detail Data

**Files:**
- Modify: `backend/app/database/seeders/stock_detail.py`
- Modify: `backend/app/database/seed_data/stock_detail.csv`
- Modify: `backend/tests/database/test_seeders.py`

- [ ] **Step 1: Add a failing seeder test for detail rows**

In `backend/tests/database/test_seeders.py`, extend the stock detail seeder test to assert SQL contains:

```python
assert "INSERT INTO forecast_line_points" in sql
assert "INSERT INTO forecast_candlesticks" in sql
assert "INSERT INTO prediction_key_factors" in sql
```

- [ ] **Step 2: Run seeder tests to verify failure**

Run: `cd backend && pytest tests/database/test_seeders.py -v`

Expected: FAIL because the seeder does not insert detail rows.

- [ ] **Step 3: Add JSON columns to seed CSV**

Add columns to `backend/app/database/seed_data/stock_detail.csv` named `forecast_line_points`, `forecast_candlesticks`, and `prediction_key_factors`. Use compact JSON per row, for example AAPL:

```csv
[{"sequence":1,"timestamp":"2026-06-02T16:15:00Z","expected_value":215.0,"lower_bound":210.0,"upper_bound":220.0}]
[{"sequence":1,"timestamp":"2026-06-02T16:15:00Z","open":214.35,"high":220.0,"low":210.0,"close":215.0}]
[{"factor_type":"momentum","source_reference_type":"market_snapshot","source_id":null,"label":"Recent price momentum","value":0.8,"rationale":"Derived from observed prices.","polarity":"positive","weight":0.45}]
```

Keep labels/rationales informational and avoid `buy`, `sell`, `hold`, and `recommend`.

- [ ] **Step 4: Insert detail rows in the seeder**

In `backend/app/database/seeders/stock_detail.py`, import `json` and after `prediction_runs` insert, use `RETURNING id` so `prediction_run_id = cursor.fetchone()[0]`. Parse each JSON column and insert detail rows with the same SQL shapes from Task 4.

- [ ] **Step 5: Run seeder tests**

Run: `cd backend && pytest tests/database/test_seeders.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

Run: `git add backend/app/database/seeders/stock_detail.py backend/app/database/seed_data/stock_detail.csv backend/tests/database/test_seeders.py && git commit -m "feat: seed forecast detail rows"`

---

### Task 7: OpenAPI And Mobile Type Refresh

**Files:**
- Modify: `mobile/src/api/generated/openapi.json`
- Modify: generated files under `mobile/src/api/generated/models/`
- Possibly modify: `mobile/src/api/generated/index.ts`

- [ ] **Step 1: Run backend tests before contract generation**

Run: `cd backend && pytest -v`

Expected: PASS.

- [ ] **Step 2: Regenerate OpenAPI JSON**

Run: `cd backend && PYTHONPATH=. python -m app.openapi ../mobile/src/api/generated/openapi.json`

Expected: `mobile/src/api/generated/openapi.json` changes and includes schemas for `StockDetailForecastLinePoint`, `StockDetailForecastCandlestick`, and `StockDetailKeyFactor`.

- [ ] **Step 3: Regenerate mobile TypeScript client**

Run: `cd mobile && npm run generate:api`

Expected: generated model files update without manual edits.

- [ ] **Step 4: Typecheck mobile**

Run: `cd mobile && npm run typecheck`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add mobile/src/api/generated && git commit -m "chore: refresh stock detail api client"`

---

### Task 8: Final Verification

**Files:**
- No source edits expected unless verification exposes gaps.

- [ ] **Step 1: Run full backend test suite**

Run: `cd backend && pytest -v`

Expected: PASS.

- [ ] **Step 2: Run mobile typecheck**

Run: `cd mobile && npm run typecheck`

Expected: PASS.

- [ ] **Step 3: Inspect generated API for recommendation language**

Run: `python - <<'PY'
from pathlib import Path
text = Path('mobile/src/api/generated/openapi.json').read_text().lower()
for forbidden in ('buy', 'sell', 'hold', 'recommendation framing'):
    if forbidden in text:
        raise SystemExit(f'Forbidden phrase found: {forbidden}')
print('ok')
PY`

Expected: `ok`. If this fails only because the disclaimer says `recommendations`, keep the disclaimer and instead add a targeted backend test proving generated labels/rationales avoid trading recommendation language.

- [ ] **Step 4: Review diff**

Run: `git diff --stat HEAD~8..HEAD`

Expected: changes are limited to forecast module, persistence/schema/API tests, seed data, and generated mobile API files.

---

## Self-Review Against Spec

- Forecast generation consumes observed source inputs and excludes prior Stock Predictions: Task 1 and Task 2.
- All canonical Forecast Horizons generate valid output shapes: Task 2.
- Line Forecast points include timestamp, expected value, lower bound, and upper bound: Task 2, Task 3, Task 5.
- Bounds surround expected values: Task 2.
- Candlestick Forecast data derives from predicted path and uncertainty: Task 2.
- Stock Prediction includes direction, confidence, expected change percent, Risk Level, and Key Factor inputs: Task 2, Task 4, Task 5.
- Forecast source links remain separate and do not link to Prediction Runs: Task 3 and Task 4.
- Persistence writes forecast detail rows, candlestick rows, source links, prediction rows, and key factor rows: Task 4.
- Stock Detail exposes generated forecast data and structured Key Factor inputs: Task 5.
- Generated TypeScript client is refreshed after OpenAPI changes: Task 7.
- Missing optional Company News and External Factors do not block generation: Task 2.
- Recommendation language is absent from generated labels/API copy other than the existing disclaimer language: Task 2, Task 5, Task 8.

## Known Execution Notes

- Task 4 intentionally calls out a likely transaction issue: the existing repository method commits internally. If detailed persistence must be atomic, refactor the existing method into a private helper instead of keeping nested commits.
- Because the repository currently has only the initial migration, modifying `0001_initial_persistence_schema.py` is consistent with the existing prototype pattern. If this schema has already been applied outside local dev, create a new Alembic revision instead.
- If generated OpenAPI client files are absent or stale, run `npm install` in `mobile/` before `npm run generate:api`.
