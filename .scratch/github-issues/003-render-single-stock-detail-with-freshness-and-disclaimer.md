---
title: Render single-Stock detail with freshness and disclaimer
labels: ready-for-agent
---

## What to build

Deliver the first combined stock-detail API response and mobile Stock Detail screen for a selected primary Stock. The screen should show Stock identity, current or latest price context, market data freshness, an informational disclaimer, and a Stock Prediction card without buy/sell/hold recommendation language.

## Acceptance criteria

- [ ] The backend exposes a combined stock-detail endpoint for one primary Stock and a selected Forecast Horizon.
- [ ] Stock Detail renders ticker, company name, exchange when available, current/latest price, and daily change.
- [ ] Market data, forecast, and prediction freshness timestamps or labels are visible.
- [ ] A compact informational disclaimer makes clear that outputs are estimates, not financial advice or trading recommendations.
- [ ] The Stock Prediction card includes direction, confidence, expected change, and Risk Level using only `bullish`, `bearish`, or `neutral` direction language.
- [ ] API and UI do not use buy, sell, or hold recommendation language.

## Blocked by

- #2
