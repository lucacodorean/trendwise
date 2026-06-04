---
title: Add observability, anonymous analytics, and rate limits
labels: ready-for-agent
---

## What to build

Add backend-first observability, minimal anonymous product analytics, and protective rate limits. Instrument technical seams without vendor lock-in, keep analytics internal, and protect repeated expensive provider/model requests.

## Acceptance criteria

- [ ] OpenTelemetry instruments FastAPI requests, Celery jobs, provider calls, and model refresh/retraining operations.
- [ ] Local OpenTelemetry Collector configuration exists under infrastructure config.
- [ ] Production observability export is configurable and not vendor-locked.
- [ ] Anonymous analytics ingestion does not require accounts or direct user identity.
- [ ] Raw anonymous analytics events are retained for 90 days.
- [ ] Rate limits protect repeated stock detail, news refresh, and provider-expensive requests.
- [ ] Excessive requests receive a clear throttling response.

## Blocked by

- #3
- #5
- #12
