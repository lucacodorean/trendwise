# ADR 0002: Modular Monolith With PostgreSQL, Celery, And Redis

## Status

Accepted

## Context

The application needs an API, market/news ingestion, forecast refresh jobs, weekly model retraining, admin tooling, and durable historical data. Splitting these responsibilities into separate deployable services would add operational complexity before the prototype needs it.

## Decision

Build one modular Python backend codebase with separate internal modules for API, domain logic, providers, storage, ML, jobs, and admin CLI.

Use PostgreSQL as the primary durable database.

Use Celery for background jobs and scheduled work, with Redis as Celery broker/result backend.

Use local filesystem volumes for prototype model artifacts, with metadata stored in PostgreSQL.

## Consequences

The prototype can run locally with Docker Compose and remain easy to reason about.

PostgreSQL stores durable Market Snapshots, Forecast Runs, Prediction Runs, provider records, model metadata, job status, and anonymous analytics events.

Redis remains transient job infrastructure rather than the source of truth for forecasts or snapshots.

If market snapshot volume grows, TimescaleDB or another time-series storage strategy can be reconsidered based on measured need.
