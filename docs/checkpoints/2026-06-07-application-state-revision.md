# Application State Revision - 2026-06-07

## Executive State

Trendwise is now a runnable local prototype with a meaningful backend domain foundation, durable persistence, Yahoo provider adapters, a Stock Detail API, and a deterministic baseline forecasting pipeline. The application is not yet a live end-to-end forecasting product: the mobile UI currently reads seeded database rows unless ingestion and generation are explicitly invoked by backend code or scripts.

The most important current distinction is this:

- Implemented: infrastructure, persistence, provider adapters, baseline forecasting logic, Stock Detail API shape, generated mobile API types.
- Not implemented yet: automatic live refresh jobs, full internet-backed forecast generation on user request, trained ML model promotion, graph visualization, Stock Summaries, and production-grade CI/observability.

## Completed Capabilities

### Local Infrastructure

- Docker Compose starts FastAPI backend, PostgreSQL, Redis, Celery worker, Celery scheduler, OpenTelemetry Collector, and Jaeger.
- `./scripts/dev expo` starts the backend stack, runs migrations, seeds local data, and launches Expo against the LAN backend URL.
- Local setup details are documented in `README.md`.

### Persistence

- PostgreSQL schema exists for supported Stocks, Market Snapshots, Forecast Runs, Prediction Runs, Forecast source links, Company News, External Factors, model versions, job statuses, and analytics placeholders.
- Forecast detail persistence now has its own migration revision for existing databases: `backend/migrations/versions/0002_forecast_detail_outputs.py`.
- The follow-up migration fix matters because issue 6 originally changed the already-applied initial migration; existing local databases needed a new Alembic revision.

### Provider Adapters

- Yahoo market data and company news adapters exist under `backend/app/providers/`.
- Provider validation covers malformed, stale, future, mismatched, and incomplete market/news data cases.
- Provider adapters are not yet automatically wired into a scheduled refresh pipeline for the user-facing Stock Detail screen.

### Stock Search And Detail API

- `/stocks/search` returns supported stocks from the database.
- `/stocks/{ticker}/detail?horizon=...` returns stock identity, market data, forecast section, prediction section, key factors, and disclaimer.
- The endpoint exposes generated forecast-compatible fields: line forecast points, candlesticks, prediction direction/confidence/expected change/risk, and structured key factor inputs.
- OpenAPI is the backend source of truth, with generated mobile TypeScript client files under `mobile/src/api/generated/`.

### Baseline Forecasting Pipeline

- `backend/app/forecasts/` contains domain models, deterministic baseline forecast generation, and a small orchestration module.
- The baseline model is ML-compatible in shape but is not a trained ML model.
- It uses latest observed price, recent close-to-close returns, historical volatility, horizon-specific schedules, and deterministic uncertainty ranges.
- It produces line points, derived candlesticks, Stock Prediction values, and structured key factors.
- Validation rejects unsupported horizons, non-positive/non-finite prices, malformed historical closes, timezone-naive observations, and stale inputs when a max age is supplied.

## Current Runtime Reality

### What Users See Locally

The local app currently shows seeded stock detail data for supported stocks such as AAPL, MSFT, NVDA, and TSLA after migrations and seeders run.

The Stock Detail endpoint does not automatically fetch Yahoo data and compute a fresh forecast every time the mobile app opens a stock. Provider adapters and forecast generation exist, but there is not yet a refresh orchestration path that continuously keeps Stock Detail data live.

### What Is Internet-Backed Today

- Yahoo provider adapter code can fetch and normalize internet-backed Market Data and Company News.
- Tests validate provider behavior using fixtures/fakes, not live network calls.
- The running local Stock Detail screen is database-backed, not guaranteed live from the internet.

### What Is ML Today

- There is no trained model yet.
- The current model is a deterministic baseline designed behind a replaceable interface.
- This is intentional and matches ADR 0004’s direction to support future trained-model validation and promotion without pretending the baseline is predictive ML.

## Known Gaps And Risks

### Live Data Flow

- No scheduled refresh job currently ingests Yahoo Market Snapshots and Company News into the local database for all tracked stocks.
- No user-triggered backend endpoint currently runs the provider-to-forecast pipeline on demand for Stock Detail.
- Forecast source audit links exist, but their live population needs to be exercised once refresh jobs are implemented.

### Frontend Experience

- Mobile API types are generated for forecast line points and candlesticks.
- Forecast graph visualization is not yet implemented.
- Offline, cached, and partial-data states are not yet implemented.
- The current mobile experience is useful for validating API contract shape, not for evaluating final product UX.

### Forecast Quality

- Baseline outputs are deterministic and testable, but not validated for real predictive value.
- No model training, backtesting, validation gates, or weekly retraining exists yet.
- Risk and confidence values are heuristic and should be presented as informational estimates only.

### Documentation Accuracy

- `README.md` still says the project is in prototype planning. That status is now stale relative to the implemented local prototype foundation.
- This checkpoint should be treated as the more accurate current state until the README is revised.

### Migration Discipline

- Future schema changes should use new Alembic revisions once a migration may have been applied locally or remotely.
- Avoid editing already-applied migrations unless the project is intentionally resetting all local database volumes.

## Verification Snapshot

Recently verified during issue 6 and follow-up debugging:

- Backend full test suite in the issue branch: `.venv/bin/python -m pytest -v` -> `107 passed`.
- Mobile typecheck in the issue branch: `npm run typecheck` -> passed.
- After the migration fix on `master`: `python3 -m pytest tests/storage/test_migrations.py tests/database/test_seeders.py -v` -> `12 passed`.
- Local runtime check after migration/seed fix: `GET /stocks/AAPL/detail?horizon=1d` returned `200 OK` with `access-control-allow-origin: http://localhost:8081`.

These checks prove the local backend route, CORS path, migration tests, and seeders work after applying migrations. They do not prove live Yahoo-backed forecast freshness or trained-model quality.

## Recommended Next Checkpoints

### Checkpoint 1: Live Data Refresh Readiness

Evaluate whether the app can ingest Yahoo Market Data and Company News into persistence for supported stocks, then run baseline forecast generation from those observed sources.

Relevant future issue area: refresh jobs, tracked stock rules, and admin CLI.

### Checkpoint 2: Forecast Graph Contract Readiness

Evaluate whether line points and candlesticks are sufficient for the mobile graph components, including historical context and visual separation between observed and forecasted values.

Relevant future issue area: line and candlestick forecast graphs.

### Checkpoint 3: Grounded Summary Readiness

Evaluate how Market Snapshots, Company News, External Factors, Forecasts, and Key Factor inputs should feed Stock Summaries without crossing into recommendation language.

Relevant future issue area: grounded stock summaries and key factors.

### Checkpoint 4: Operational Readiness

Evaluate CI, OpenAPI drift checks, observability, rate limits, and failure reporting before treating the prototype as a reliable demo environment.

Relevant future issue area: CI, observability, legal/settings/cache work.

## Reference Artifacts

- Current domain glossary: `CONTEXT.md`
- Product overview: `docs/product-v1.md`
- Task breakdown: `docs/tasks-v1.md`
- ADR 0003: `docs/adr/0003-forecast-grounding-market-snapshots.md`
- ADR 0004: `docs/adr/0004-ml-strategy-and-validation.md`
- Issue 6 design: `docs/superpowers/specs/2026-06-06-issue-6-baseline-forecasting-design.md`
- Issue 6 implementation plan: `docs/superpowers/plans/2026-06-06-issue-6-baseline-forecasting.md`
- Issue 6 handoff: `docs/handsoff/issue-6-handoff.md`
