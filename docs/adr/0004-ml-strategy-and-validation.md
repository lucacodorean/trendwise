# ADR 0004: ML Strategy And Validation-Gated Retraining

## Status

Accepted

## Context

The prototype should use ML from day one for numeric forecasts and predictions. Different Forecast Horizons depend on different signals, while fully separate per-stock and per-horizon models would increase operational complexity and data requirements.

The app also needs a safe way to improve models without silently degrading forecast quality.

## Decision

Use a shared model architecture with a global base model across supported stocks and horizon-specific model heads or outputs.

Allow optional stock-specific fine-tuning or calibration when enough data exists.

The model outputs explicit forecast steps for graph rendering, including uncertainty ranges. Candlestick Forecasts are derived from predicted price paths plus volatility/range estimates in the prototype.

Run scheduled weekly retraining. New candidate models are promoted only if validation passes. If training or validation fails, keep the current promoted model.

Use an LLM API only for Stock Summaries and Key Factors, not numeric forecasts or prediction values.

## Consequences

The model can learn common patterns across stocks while still specializing outputs by Forecast Horizon.

Forecast graph paths reflect model output rather than frontend interpolation.

Validation-gated promotion reduces the risk of automated retraining degrading user-facing forecasts.

The LLM boundary keeps numeric forecasting reproducible and measurable while still allowing useful natural-language explanations.
