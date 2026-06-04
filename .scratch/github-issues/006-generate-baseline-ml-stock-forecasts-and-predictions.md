---
title: Generate baseline ML Stock Forecasts and Predictions
labels: ready-for-agent
---

## What to build

Implement the first ML-compatible forecasting and prediction pipeline. The pipeline should generate full forecast steps, uncertainty ranges, Line Forecast data, derived Candlestick Forecast data, Stock Prediction values, and structured Key Factor inputs without using prior Stock Predictions as forecast evidence.

## Acceptance criteria

- [ ] Forecast generation consumes Market Snapshots, historical prices, External Factors, Company News, and model logic, not prior Stock Predictions.
- [ ] Every forecast point includes timestamp or interval, expected value, lower bound, and upper bound.
- [ ] Candlestick Forecast data is derived from predicted path and uncertainty/range estimates.
- [ ] Stock Prediction includes direction, confidence, expected change, Risk Level, and Key Factor inputs.
- [ ] Prediction language avoids buy, sell, hold, winner, or best-stock recommendation framing.
- [ ] ML pipeline tests verify output shape for all canonical Forecast Horizons.

## Blocked by

- #4
- #5
