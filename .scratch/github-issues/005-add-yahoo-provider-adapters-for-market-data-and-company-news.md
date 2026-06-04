---
title: Add Yahoo provider adapters for market data and Company News
labels: ready-for-agent
---

## What to build

Fetch normalized market data, basic company metadata, and Company News through replaceable provider adapters. Yahoo Finance is the prototype provider, but API routes and domain logic should depend on provider interfaces rather than direct provider calls.

## Acceptance criteria

- [ ] Market data, Company News, and summary generation seams are represented as provider interfaces.
- [ ] Yahoo market adapter returns normalized historical prices, latest price, previous close, basic metadata, and market status when available.
- [ ] Yahoo news adapter returns compact news metadata suitable for Company News cards.
- [ ] Provider handling respects supported Stock restrictions and raw news licensing boundaries.
- [ ] Provider tests cover normalized successful responses and missing, stale, or malformed provider data.

## Blocked by

- #4
