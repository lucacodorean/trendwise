---
title: Add Line and Candlestick Forecast Graphs
labels: ready-for-agent
---

## What to build

Render Forecast Graphs for a single Stock with historical price context and a clearly separated forecast segment. Line Forecast should be the first-use default, Candlestick Forecast should be selectable, and graph type preference should persist locally.

## Acceptance criteria

- [ ] Single-stock graph uses actual price values rather than normalized comparison movement.
- [ ] Historical and forecasted values are visually distinct.
- [ ] Line Forecast is the default graph type on first use.
- [ ] Candlestick Forecast can be selected and uses backend-provided derived OHLC forecast data.
- [ ] Forecast uncertainty is visible through expected values and uncertainty ranges.
- [ ] Graph type preference persists locally across app restarts.
- [ ] Extended-hours movement is shown only if visually distinct and labeled, or omitted from the prototype.

## Blocked by

- #6
- #7
