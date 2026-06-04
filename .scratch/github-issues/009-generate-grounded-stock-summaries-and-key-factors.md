---
title: Generate grounded Stock Summaries and Key Factors
labels: ready-for-agent
---

## What to build

Generate and render Stock Summaries and Key Factors from structured backend inputs. OpenAI may be used only through a summary adapter and only for grounded explanation text; deterministic fallback summaries must keep the Stock Detail screen useful when OpenAI is unavailable.

## Acceptance criteria

- [ ] OpenAI summary adapter receives only structured inputs from Market Snapshots, Company News, External Factors, Stock Forecasts, and Stock Predictions.
- [ ] OpenAI does not generate numeric forecast values, prediction direction, confidence, expected change, or Risk Level.
- [ ] Missing OpenAI configuration or failed calls return deterministic fallback Stock Summaries and Key Factors.
- [ ] Stock Summary appears before Company News on the mobile Stock Detail screen.
- [ ] Company News cards show title, source, date/time, snippet, and source-opening action.
- [ ] Five Company News items show by default with a `Show more` affordance for additional relevant items.
- [ ] Key Factors are grounded and traceable to structured inputs.

## Blocked by

- #5
- #6
- #7
