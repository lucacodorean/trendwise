---
title: Support canonical Forecast Horizons end to end
labels: ready-for-agent
---

## What to build

Support the canonical Forecast Horizons across domain validation, backend responses, mobile selection, cached local preference, graph data, Stock Prediction, Stock Summary inputs, news windows, and External Factor weighting.

## Acceptance criteria

- [ ] Allowed Forecast Horizons are exactly `30m`, `1d`, `5d`, `7d`, `1mo`, `6mo`, and `1y`.
- [ ] Ambiguous or unsupported values such as `1M`, `30M`, and `2d` are rejected.
- [ ] Default Forecast Horizon is `1d`.
- [ ] `30m`, `1d`, and `5d` are interpreted using regular-market trading time where required.
- [ ] `7d`, `1mo`, `6mo`, and `1y` use calendar periods represented through trading-session price points.
- [ ] Changing Forecast Horizon updates graph, prediction, summary inputs, news window, and External Factor weighting together.
- [ ] Mobile persists the last selected Forecast Horizon locally.

## Blocked by

- #6
