---
title: Handle offline, cached, and partial data states
labels: ready-for-agent
---

## What to build

Support limited offline and partial-data behavior for the mobile app. Cached detail can be displayed read-only with clear labels, backend-dependent actions should be disabled offline, and available forecast/prediction or news data should still render when the other data class is unavailable.

## Acceptance criteria

- [ ] Mobile stores the last loaded primary Stock detail for limited offline display.
- [ ] Offline cached detail is clearly labeled as cached/offline.
- [ ] Search, compare add, refresh, and backend-dependent actions are disabled offline.
- [ ] Mobile never generates forecasts locally offline.
- [ ] If forecast/prediction data is unavailable but news exists, the screen shows forecast unavailable messaging and renders available Company News.
- [ ] If news is unavailable but forecast/prediction data exists, the screen renders forecast/prediction normally and shows a news unavailable state.
- [ ] Stale forecasts are clearly labeled and forecasts are unavailable when Market Snapshots are beyond the configured freshness cutoff.

## Blocked by

- #3
- #8
- #9
- #10
