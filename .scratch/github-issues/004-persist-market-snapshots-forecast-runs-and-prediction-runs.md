---
title: Persist Market Snapshots, Forecast Runs, and Prediction Runs
labels: ready-for-agent
---

## What to build

Add durable PostgreSQL persistence for observed Market Snapshots and computed Forecast Runs and Prediction Runs, preserving the domain boundary that forecasts are grounded in observed data and not prior predictions.

## Acceptance criteria

- [ ] PostgreSQL models and migrations represent supported Stocks, Market Snapshots, Forecast Runs, Prediction Runs, Company News records, External Factor records, Model Versions, job statuses, and anonymous analytics events.
- [ ] Market Snapshots are stored separately from computed Stock Forecasts and Stock Predictions.
- [ ] Forecast Runs and Prediction Runs are linked to Stock, Forecast Horizon, source inputs, generated timestamps, and model metadata where applicable.
- [ ] Repository tests can store and retrieve a Market Snapshot, Forecast Run, and Prediction Run linked to the same Stock and Forecast Horizon.
- [ ] Persistence design supports historical retention for Forecast Runs and Market Snapshots where licensing permits.

## Blocked by

- #3
