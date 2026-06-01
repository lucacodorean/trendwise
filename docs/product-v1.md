# Trendwise Prototype Product Decisions

## Status

This document describes the agreed off-production prototype scope. The application is not a trading advisor and does not provide buy, sell, or hold recommendations.

## Product Shape

The product is a native mobile stock analysis app with a Python backend and an Expo React Native frontend. The app displays Stock Forecasts, Stock Predictions, Stock Summaries, Company News, and Key Factors for supported US-listed common stocks.

The prototype is free, has no user accounts, no subscriptions, no ads, no watchlists, and no notifications.

## Supported Stocks

The prototype supports selected US-listed common stocks, initially constrained to a controlled search universe such as S&P 500 stocks and optionally high-volume NASDAQ/NYSE common stocks.

Unsupported in the prototype:

- ETFs such as `SPY` and `QQQ`
- OTC securities
- Warrants
- Preferred shares
- Funds
- Delisted symbols
- Non-US exchanges

Users select stocks from supported search results only. Free-text unsupported ticker submission is not part of the prototype.

## Forecast Horizons

Canonical Forecast Horizons are:

- `30m`
- `1d`
- `5d`
- `7d`
- `1mo`
- `6mo`
- `1y`

Default Forecast Horizon is `1d`.

Interpretation:

- `30m` means the next 30 minutes of regular market trading time.
- `1d` means the next trading day.
- `5d` means the next 5 trading days.
- `7d` means the next 7 calendar days, represented through trading-session price points.
- `1mo`, `6mo`, and `1y` are calendar periods represented through trading days inside those periods.

When `30m` is selected outside regular market hours, the app forecasts the next 30 minutes after the next regular market open.

## Forecasts And Predictions

A Stock Forecast is a projected future price behavior for a Stock over a Forecast Horizon. It is grounded in observed Market Snapshots, historical prices, External Factors, Company News, and model logic. It must not be based on prior Stock Predictions.

A Stock Prediction is a discrete analytical signal for a Stock over a Forecast Horizon. It includes:

- Direction: `bullish`, `bearish`, or `neutral`
- Confidence
- Expected change
- Risk Level
- Key Factors

The app never presents Stock Predictions as trading recommendations.

## Forecast Graphs

The Forecast Graph displays historical price context leading into a clearly separated forecast segment.

Supported graph types:

- Line Forecast, default on first use
- Candlestick Forecast, optional user preference

Every forecast point should include an expected value and uncertainty range. Candlestick Forecasts are derived from the predicted price path plus volatility/range estimates in the prototype.

Single-stock detail graphs use actual price values. Multi-stock comparison graphs use normalized percentage movement by default, including candlestick comparison.

Historical and forecasted values must be visually distinct. Extended-hours movement may be shown in single-stock detail only if clearly labeled and styled differently. Comparison graphs default to regular-session display.

## Stock Selection And Comparison

The app launches to the last selected primary Stock when locally cached. If no primary Stock is cached, the app opens Stock Search.

The user first selects exactly one primary Stock. The app opens that Stock's detail/results screen. From there, the user can tap `Compare with` and add up to two comparison Stocks.

Comparison rules:

- Maximum selected Stocks in a comparison: 3
- One primary Stock plus up to two comparison Stocks
- All selected Stocks share the same Forecast Horizon
- Each selected Stock has its own Stock Prediction
- No combined winner or best-stock recommendation is produced
- Each graph series can be hidden independently in the UI
- Graph visibility is frontend-only session state
- Removing all comparison Stocks returns to single-stock detail mode
- Changing the primary Stock clears comparison Stocks

## Stock Detail Screen

Top section:

- Stock identity: ticker, company name, exchange when available
- Current or latest market price and daily change
- Market data freshness/status
- Forecast Horizon selector
- Compact informational disclaimer
- Stock Prediction card
- Forecast Graph
- Stock Summary
- Company News

The Stock Prediction card appears above the Forecast Graph and includes direction, confidence, expected change, Risk Level, and 3-5 Key Factors.

The Stock Summary appears before Company News. Company News uses compact cards with title, source, date/time, short snippet, and source-opening action. Show 5 news items by default with `Show more` for additional relevant items.

In comparison mode:

- Compact prediction cards for all selected Stocks appear above the comparison graph
- The comparison graph displays selected Stocks for the shared Forecast Horizon
- The user can switch the active Stock for Stock Summary and Company News
- Stock Summary and Company News are shown for the active Stock only

## News, Summaries, And External Factors

Company News is listed separately and synthesized into the Stock Summary. News freshness is updated when a user accesses a Stock.

News windows are horizon-aware:

- `30m`: last 24 hours
- `1d`: last 3 days
- `5d`: last 14 days
- `7d`: last 21 days
- `1mo`: last 60 days
- `6mo`: last 12 months
- `1y`: last 24 months

External Factors are horizon-aware. They include company news, earnings events, macroeconomic indicators, sector movement, market sentiment, analyst ratings when available, and major geopolitical or regulatory events.

Social media sentiment is excluded from the prototype. News sentiment may be derived from company news.

Stock Summaries and Key Factors may be generated by an LLM API, but must be grounded only in backend-provided structured inputs. The LLM must not invent prices, directions, confidence, risk, or news facts.

## Data Freshness

Market Snapshots are observed real-world market data stored separately from computed Stock Forecasts.

Snapshot frequency:

- Daily market-close snapshots for tracked/requested Stocks
- Intraday snapshots for `30m` when requested or actively tracked

Forecasts and Predictions are refreshed during each Stock's market-closed window. All canonical Forecast Horizons are generated for tracked/requested Stocks during the closed-market refresh.

A Stock is tracked when it has been requested as a primary or comparison Stock in the last 30 days.

If fresh market data is unavailable, the app may show stale results only when clearly labeled. If the underlying Market Snapshot is too old beyond a configured cutoff, a new forecast is not generated and the app shows forecast unavailable.

## Machine Learning

The prototype uses ML from day one for numeric Stock Forecasts and Stock Predictions.

ML strategy:

- Shared model architecture
- Global base model across supported stocks
- Horizon-specific model heads or outputs
- Optional stock-specific fine-tuning or calibration when enough data exists
- Full forecast steps for graph rendering, not endpoint-only interpolation
- Confidence combines model probability, forecast uncertainty, calibration, data quality, and signal agreement

Model retraining runs weekly. Candidate models must pass validation before promotion. Failed training or validation keeps the current promoted model.

## Providers And Infrastructure Scope

The prototype is off-production.

Initial providers:

- Market data and basic company metadata: Yahoo Finance through a provider adapter
- Company News: Yahoo Finance news through a provider adapter when available
- Summaries and Key Factors: OpenAI API
- Deterministic fallback for summaries if the LLM API key is missing or the call fails

Provider adapters are required so Yahoo Finance and OpenAI can be replaced later.

## Local State

The frontend caches locally:

- Last selected primary Stock
- Last selected Forecast Horizon
- Graph type preference
- Last loaded stock detail for limited offline display

The frontend does not persist:

- Comparison Stocks across app restarts
- Hidden graph series state across app restarts

Clearing local cache removes the remembered primary Stock, Forecast Horizon, graph type preference, and cached stock detail data.

## Offline And Partial Data

Offline mode is read-only and limited. If cached last primary Stock detail exists, show it with an offline/cached label. Disable refresh, search, compare add, and backend-dependent actions. Forecasts are never generated locally.

If forecast/prediction data is unavailable but news is available, show partial stock detail with forecast unavailable messaging and Company News.

If news is unavailable but forecast/prediction data is available, show forecast/prediction normally and show a news unavailable state.

## Observability And Analytics

OpenTelemetry is used for backend observability first:

- API latency
- Backend errors
- Celery job duration/failures
- Provider API failures
- Model refresh/retraining health

Frontend uses basic error/performance logging in the prototype.

Minimal anonymous product analytics are stored internally, not through a third-party analytics vendor. Raw anonymous analytics events are retained for 90 days. Aggregated metrics may be retained longer.

## Legal And Privacy

The app includes:

- Privacy Policy
- Terms/Disclaimer
- Financial information disclaimer

Documents are available both in-app and as public hosted pages when the app moves beyond local prototype use.
