---
title: Implement Stock Comparison with normalized graph data
labels: ready-for-agent
---

## What to build

Extend Stock Detail into Stock Comparison by allowing a primary Stock plus up to two comparison Stocks. The backend should return comparison data through the same stock-detail endpoint, including backend-normalized percentage graph series. The UI should avoid ranking or recommending selected Stocks.

## Acceptance criteria

- [ ] `Compare with` is available from the Stock Detail header and near graph controls.
- [ ] `Compare with` opens a bottom sheet that can add up to two comparison Stocks.
- [ ] Comparison selection follows supported Stock restrictions and rejects duplicate comparison Stocks or primary-as-comparison selection.
- [ ] All selected Stocks share one Forecast Horizon and one graph type.
- [ ] Each selected Stock has its own Stock Prediction card.
- [ ] Backend returns normalized percentage graph data for comparison, including candlestick comparison when selected.
- [ ] The UI can hide or show graph series independently without removing prediction summaries.
- [ ] Hidden graph state and comparison Stocks are not persisted across app restarts.
- [ ] Removing all comparison Stocks returns to single-stock detail mode.
- [ ] No winner, rank, best-stock, buy, sell, or hold recommendation is produced.

## Blocked by

- #2
- #6
- #8
