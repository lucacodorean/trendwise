# Issue 6 Baseline Forecasting Design

## Context

Issue 6 adds the first ML-compatible Stock Forecast and Stock Prediction pipeline. The implementation should produce deterministic baseline outputs now while keeping the module boundaries suitable for a trained model later.

This design follows the accepted project decisions:

- ADR 0003: Stock Forecasts are grounded in Market Snapshots, historical prices, External Factors, Company News, and model logic. Forecasts must not use prior Stock Predictions as evidence.
- ADR 0004: numeric forecasts and prediction values come from model logic, forecast graph paths reflect model output, and Candlestick Forecasts are derived from predicted paths plus volatility or range estimates.

## Scope

Build a backend forecasting pipeline for every canonical Forecast Horizon: `30m`, `1d`, `5d`, `7d`, `1mo`, `6mo`, and `1y`.

The pipeline must generate:

- Line Forecast points with timestamp or interval, expected value, lower bound, and upper bound.
- Candlestick Forecast data derived from the predicted path and uncertainty or range estimates.
- Stock Prediction values: direction, confidence, expected change percent, and Risk Level.
- Structured Key Factor inputs that can later feed Stock Summaries and natural-language Key Factors.

The pipeline should not produce polished LLM prose. It should not introduce buy, sell, hold, winner, best-stock, or recommendation framing.

## Recommended Approach

Use a hybrid baseline:

- The first implementation is deterministic and testable.
- The forecasting component is shaped like a model interface so a trained model can replace it later.
- Providers and repositories stay separate from forecasting logic.

This avoids pretending to have a useful trained model before validation exists while still honoring the ML-oriented architecture from ADR 0004.

## Backend Components

Add a forecasting module, likely under `backend/app/forecasts/`.

### Forecast Input

Create a single input object for generation with:

- Supported Stock identity.
- Forecast Horizon.
- Latest Market Snapshot values.
- Historical price points.
- Company News items.
- External Factor inputs when available.

The input should contain observed source data only. It must not include prior Stock Predictions.

### Baseline Forecast Model

Create a deterministic model-compatible component that produces forecast steps.

The baseline can use:

- Latest price as the starting point.
- Recent return as the directional signal.
- Historical close-to-close volatility as uncertainty.
- Horizon-specific step schedules and volatility scaling.
- A neutral fallback when history is too short.

Each output point must include an interval or timestamp, expected value, lower bound, and upper bound. Bounds must surround the expected value.

### Candlestick Deriver

Derive Candlestick Forecast data from the line forecast path and uncertainty range. The prototype does not need independent OHLC prediction.

Each forecast candle should include interval or timestamp, open, high, low, and close. Open and close come from adjacent expected path values; high and low are widened by the interval uncertainty estimate.

### Prediction Deriver

Derive Stock Prediction values from the forecast path and uncertainty:

- Direction: `bullish`, `bearish`, or `neutral`.
- Expected change percent: final expected value versus latest observed price.
- Confidence: bounded value based on signal strength relative to uncertainty.
- Risk Level: `low`, `medium`, or `high`, based on forecast uncertainty and recent volatility.

Prediction language and labels must remain informational and must not use trading recommendation language.

### Key Factor Inputs

Produce structured Key Factor inputs, not final prose. Suggested fields:

- factor type, such as `momentum`, `volatility`, `freshness`, `news`, or `external_factor`.
- source reference type and optional source id.
- label.
- numeric value or concise rationale.
- polarity or weight when useful.

Examples include recent momentum, volatility/risk, market data freshness, and company-news count. If sentiment is not implemented yet, represent news as presence/count/freshness rather than invented sentiment.

## Persistence

The current schema stores `forecast_runs` and `prediction_runs` summaries. Issue 6 should add detailed output persistence.

Add storage for:

- Forecast line points tied to `forecast_runs`.
- Forecast candlesticks tied to `forecast_runs`.
- Prediction key factor inputs tied to `prediction_runs`.

Keep Forecast source links separate and auditable:

- Forecasts may link to Market Snapshots, Company News, and External Factors.
- Forecasts must not link to prior Prediction Runs.

Repository methods should persist the generated forecast and prediction outputs in one transaction when possible.

## API Shape

The existing Stock Detail endpoint already returns forecast and prediction sections. For this slice, it is the mobile graph contract and should expose the generated forecast data directly:

- Forecast includes generated line points.
- Forecast includes Candlestick Forecast data.
- Prediction continues exposing direction, confidence, expected change percent, Risk Level, generated timestamp, and freshness label.
- Prediction includes structured Key Factor inputs.

Generated TypeScript client code should be refreshed after OpenAPI changes.

## Error Handling

If source market data is missing, stale, malformed, or unsupported, forecasting should fail explicitly before writing computed outputs.

If history is short but still usable, generate a neutral deterministic forecast with wider uncertainty and a lower confidence prediction.

If Company News or External Factors are unavailable, forecasts may still run from Market Snapshots and historical prices. Key Factor inputs should reflect missing optional signals rather than fabricate them.

## Testing

Add backend tests for:

- All canonical Forecast Horizons generate valid output shapes.
- Every forecast point has timestamp or interval, expected value, lower bound, and upper bound.
- Bounds surround expected values.
- Candlestick Forecast data is derived from predicted path and uncertainty ranges.
- Stock Prediction includes direction, confidence, expected change percent, Risk Level, and Key Factor inputs.
- Forecast generation consumes observed source inputs and does not read prior Stock Predictions.
- Recommendation language is absent from generated labels and API copy.
- Persistence writes forecast detail rows, candlestick rows, source links, prediction rows, and key factor input rows.

## Non-Goals

- No trained model promotion or weekly retraining in this issue.
- No LLM-generated Stock Summaries or prose Key Factors in this issue.
- No personalized financial advice or trading recommendations.
- No frontend graph visualization changes beyond generated API type compatibility unless required by OpenAPI drift tests.

## OpenAPI And Mobile Contract

Any Stock Detail schema changes must be reflected in generated mobile TypeScript API files. The backend remains the OpenAPI source of truth.

## Acceptance Mapping

- Forecast generation consumes Market Snapshots, historical prices, External Factors, Company News, and model logic: covered by Forecast Input, source links, and tests.
- Forecast points include timestamp or interval, expected value, lower bound, and upper bound: covered by Baseline Forecast Model and persistence/API tests.
- Candlestick Forecast data is derived from predicted path and uncertainty estimates: covered by Candlestick Deriver.
- Stock Prediction includes direction, confidence, expected change, Risk Level, and Key Factor inputs: covered by Prediction Deriver and Key Factor Inputs.
- Prediction language avoids recommendation framing: covered by API and copy tests.
- ML pipeline tests verify output shape for all canonical Forecast Horizons: covered by Testing.
