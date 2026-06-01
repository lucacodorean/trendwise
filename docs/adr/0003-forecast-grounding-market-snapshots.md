# ADR 0003: Forecasts Are Grounded In Market Snapshots And External Factors

## Status

Accepted

## Context

The app produces both Stock Forecasts and Stock Predictions. A feedback loop where future forecasts use prior predictions as evidence would risk amplifying the model's own assumptions instead of grounding outputs in observed market behavior.

## Decision

Stock Forecasts are generated from observed Market Snapshots, historical prices, External Factors, Company News, and model logic.

Stock Forecasts must not use prior Stock Predictions as market evidence.

Stock Predictions may summarize or be derived from Stock Forecasts and other structured signals, but predictions do not feed back into future forecasts.

Market Snapshots are stored separately from computed Stock Forecasts.

## Consequences

Forecasts remain auditable against the data available at generation time.

Wrong forecasts can be evaluated later by comparing stored Forecast Runs with later Market Snapshots.

The domain model preserves a clear distinction between observed data and computed analytical output.
