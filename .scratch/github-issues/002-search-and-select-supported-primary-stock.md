---
title: Search and select supported primary Stock
labels: ready-for-agent
---

## What to build

Allow a mobile user to search for supported US-listed common Stocks, select exactly one primary Stock, and relaunch into the last selected primary Stock when cached. Unsupported instruments should be excluded or clearly rejected, and generated mobile API types should be used for the backend contract.

## Acceptance criteria

- [ ] Stock Search opens on first launch when no cached primary Stock exists.
- [ ] Search supports ticker and company-name matching for supported US-listed common Stocks only.
- [ ] Unsupported ETFs, OTC securities, warrants, preferred shares, funds, delisted symbols, and non-US exchanges are excluded or clearly rejected.
- [ ] Selecting a primary Stock stores it locally and navigates to the Stock Detail path.
- [ ] Relaunch opens the cached primary Stock when present.
- [ ] Mobile uses generated TypeScript API types/client code from FastAPI OpenAPI.

## Blocked by

- #1
