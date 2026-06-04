---
title: Add refresh jobs, tracked Stock rules, and admin CLI
labels: ready-for-agent
---

## What to build

Add Celery-based refresh jobs, scheduler wiring, durable job status, tracked/requested Stock rules, and CLI commands for local operations. Refresh behavior should support daily market-close snapshots, intraday `30m` snapshots when relevant, fresh Company News on access, and forecast refreshes for tracked/requested Stocks.

## Acceptance criteria

- [ ] Celery uses Redis as broker/result backend while durable job status remains in PostgreSQL.
- [ ] A Stock is treated as tracked when requested as primary or comparison in the last 30 days.
- [ ] Jobs exist for market snapshot refresh, news refresh, forecast refresh, and weekly retraining trigger.
- [ ] Daily market-close refresh prepares all canonical Forecast Horizons for tracked/requested Stocks.
- [ ] Intraday snapshots are captured for `30m` when requested or actively tracked.
- [ ] Company News freshness updates when a user accesses a Stock.
- [ ] CLI includes status and operational commands for refresh health, data freshness, retraining trigger, and explicit Stock forecast refresh.
- [ ] Job tests verify status updates and failure logging.

## Blocked by

- #4
- #5
- #6
- #7
