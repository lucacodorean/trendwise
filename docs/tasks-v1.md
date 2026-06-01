# Trendwise Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an off-production stock forecasting/prediction prototype with a Python FastAPI backend, ML-driven forecasts, OpenAI-grounded summaries, and an Expo React Native mobile app.

**Architecture:** Use a monorepo with a modular Python backend, Expo mobile app, Docker Compose local infrastructure, PostgreSQL durable storage, Redis/Celery background jobs, and provider adapters. The backend owns domain/business rules and exposes combined stock-detail payloads optimized for the mobile screen.

**Tech Stack:** Python, FastAPI, PostgreSQL, Redis, Celery, SQLAlchemy or SQLModel, Alembic, pytest, Yahoo Finance adapter, OpenAI API, OpenTelemetry, TypeScript, Expo React Native, generated TypeScript API client, Docker Compose, GitHub Actions.

---

## File Structure

Create this monorepo structure:

- `backend/`: FastAPI app, domain modules, provider adapters, ML pipeline, Celery jobs, admin CLI, tests
- `mobile/`: Expo TypeScript app, screens, components, generated API client, local cache
- `infra/`: Docker, OpenTelemetry, local service configuration
- `docs/`: product decisions, ADRs, legal drafts, implementation tasks
- `.github/workflows/`: CI checks

Backend modules should be split by responsibility:

- `backend/app/api/`: HTTP routes and OpenAPI schema
- `backend/app/domain/`: Stock, Forecast Horizon, prediction, forecast, comparison rules
- `backend/app/providers/`: market data, news, LLM adapters
- `backend/app/storage/`: database models, repositories, migrations
- `backend/app/ml/`: feature generation, forecast model, validation, model registry
- `backend/app/jobs/`: Celery tasks and scheduled jobs
- `backend/app/admin/`: CLI commands
- `backend/tests/`: unit, API, provider, job, and pipeline tests

Mobile modules should be split by screen and component:

- `mobile/src/screens/StockSearchScreen.tsx`
- `mobile/src/screens/StockDetailScreen.tsx`
- `mobile/src/components/PredictionCard.tsx`
- `mobile/src/components/ForecastGraph.tsx`
- `mobile/src/components/CompareWithSheet.tsx`
- `mobile/src/components/CompanyNewsList.tsx`
- `mobile/src/components/StockSummary.tsx`
- `mobile/src/storage/localPreferences.ts`
- `mobile/src/api/generated/`: generated API client/types

## Task 1: Bootstrap Monorepo And Local Infrastructure

**Files:**

- Create: `backend/pyproject.toml`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/tests/test_health.py`
- Create: `mobile/package.json`
- Create: `mobile/app.json`
- Create: `docker-compose.yml`
- Create: `.env.example`

- [ ] **Step 1: Create backend package skeleton**

Create a minimal FastAPI app with `/health` returning service status.

- [ ] **Step 2: Write health test**

Test that `/health` returns HTTP 200 and `{ "status": "ok" }`.

Run: `cd backend && pytest backend/tests/test_health.py -v`

Expected: health test passes after implementation.

- [ ] **Step 3: Add Docker Compose services**

Define local services for `backend`, `postgres`, `redis`, `worker`, `scheduler`, `otel-collector`, and optional `jaeger`.

- [ ] **Step 4: Add frontend skeleton**

Initialize Expo TypeScript app under `mobile/` and confirm it starts outside Docker with `npm start`.

- [ ] **Step 5: Verify local startup**

Run: `docker compose up --build`

Expected: backend starts, Postgres starts, Redis starts, `/health` responds.

## Task 2: Define Domain Types And API Contracts

**Files:**

- Create: `backend/app/domain/horizons.py`
- Create: `backend/app/domain/stocks.py`
- Create: `backend/app/domain/forecasts.py`
- Create: `backend/app/domain/predictions.py`
- Create: `backend/app/api/schemas.py`
- Create: `backend/tests/domain/test_horizons.py`

- [ ] **Step 1: Implement Forecast Horizon validation**

Allowed values must be exactly `30m`, `1d`, `5d`, `7d`, `1mo`, `6mo`, and `1y`.

- [ ] **Step 2: Test invalid horizon rejection**

Run: `cd backend && pytest backend/tests/domain/test_horizons.py -v`

Expected: unsupported values like `1M`, `30M`, and `2d` fail validation.

- [ ] **Step 3: Define API schemas**

Model combined stock-detail payload with stock identity, selected horizon, forecast graph data, prediction, key factors, stock summary, company news, freshness timestamps, and optional comparison data.

- [ ] **Step 4: Generate OpenAPI**

Run backend and confirm `/openapi.json` includes stock-detail schemas.

## Task 3: Add PostgreSQL Persistence And Migrations

**Files:**

- Create: `backend/app/storage/models.py`
- Create: `backend/app/storage/session.py`
- Create: `backend/app/storage/repositories.py`
- Create: `backend/migrations/`
- Create: `backend/tests/storage/test_repositories.py`

- [ ] **Step 1: Add persistence models**

Represent supported Stocks, Market Snapshots, Forecast Runs, Prediction Runs, Company News records, External Factor records, Model Versions, job statuses, and anonymous analytics events.

- [ ] **Step 2: Add migration setup**

Use Alembic migrations for database schema changes.

- [ ] **Step 3: Test repository round trip**

Store and retrieve a Market Snapshot, Forecast Run, and Prediction Run linked to the same Stock and Forecast Horizon.

Run: `cd backend && pytest backend/tests/storage/test_repositories.py -v`

Expected: records persist with generated timestamps and relationships intact.

## Task 4: Implement Provider Adapters

**Files:**

- Create: `backend/app/providers/base.py`
- Create: `backend/app/providers/yahoo_market_data.py`
- Create: `backend/app/providers/yahoo_news.py`
- Create: `backend/app/providers/openai_summaries.py`
- Create: `backend/app/providers/template_summaries.py`
- Create: `backend/tests/providers/test_summary_fallback.py`

- [ ] **Step 1: Define provider interfaces**

Market data, news, and summary generation must be accessed through interfaces, not direct library calls from API routes.

- [ ] **Step 2: Implement Yahoo Finance prototype adapters**

Market adapter returns historical prices, latest price, previous close, basic metadata, and market status when available. News adapter returns compact news metadata.

- [ ] **Step 3: Implement OpenAI summary adapter**

Generate Stock Summary and Key Factors only from structured backend inputs.

- [ ] **Step 4: Implement deterministic fallback**

If OpenAI API key is missing or the call fails, return a grounded template summary.

- [ ] **Step 5: Test fallback behavior**

Run: `cd backend && pytest backend/tests/providers/test_summary_fallback.py -v`

Expected: missing OpenAI configuration returns deterministic summary without failing stock detail.

## Task 5: Build Forecast And Prediction Pipeline

**Files:**

- Create: `backend/app/ml/features.py`
- Create: `backend/app/ml/model.py`
- Create: `backend/app/ml/forecasting.py`
- Create: `backend/app/ml/prediction.py`
- Create: `backend/app/ml/validation.py`
- Create: `backend/tests/ml/test_forecast_pipeline.py`

- [ ] **Step 1: Build deterministic baseline ML-compatible pipeline**

Implement the first ML pipeline shape with feature generation, model inference wrapper, forecast point generation, uncertainty range generation, and prediction derivation.

- [ ] **Step 2: Output full forecast steps**

Line Forecast output must include timestamp/interval, expected value, lower bound, and upper bound for every forecast point.

- [ ] **Step 3: Derive candlestick forecast data**

Derive estimated OHLC values from forecast path and uncertainty/volatility estimates.

- [ ] **Step 4: Derive prediction summary**

Produce direction, confidence, expected change, Risk Level, and Key Factor inputs without trading recommendation language.

- [ ] **Step 5: Test pipeline output shape**

Run: `cd backend && pytest backend/tests/ml/test_forecast_pipeline.py -v`

Expected: all canonical horizons return forecast steps with uncertainty ranges and prediction fields.

## Task 6: Implement Stock Detail And Comparison API

**Files:**

- Create: `backend/app/api/routes/stocks.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/api/test_stock_detail.py`

- [ ] **Step 1: Implement supported stock search endpoint**

Return supported stocks only, searchable by ticker or company name.

- [ ] **Step 2: Implement combined stock-detail endpoint**

Accept primary stock, optional comparison stocks, and Forecast Horizon. Return one combined payload optimized for the mobile screen.

- [ ] **Step 3: Enforce comparison rules**

Reject more than two comparison stocks, duplicate primary stock, unsupported stocks, and invalid horizons.

- [ ] **Step 4: Return normalized graph data for comparison**

When comparison stocks are requested, include normalized percentage graph series from the backend.

- [ ] **Step 5: Test API behavior**

Run: `cd backend && pytest backend/tests/api/test_stock_detail.py -v`

Expected: single-stock detail and three-stock comparison payloads validate against schemas.

## Task 7: Add Background Jobs, Scheduler, And Admin CLI

**Files:**

- Create: `backend/app/jobs/celery_app.py`
- Create: `backend/app/jobs/tasks.py`
- Create: `backend/app/admin/cli.py`
- Create: `backend/tests/jobs/test_jobs.py`

- [ ] **Step 1: Configure Celery with Redis**

Use Redis as broker/result backend. Keep durable job status in PostgreSQL.

- [ ] **Step 2: Implement refresh jobs**

Add jobs for market snapshots, news refresh, forecast refresh, and weekly retraining trigger.

- [ ] **Step 3: Implement validation-gated model promotion command**

Candidate models must pass validation before becoming promoted.

- [ ] **Step 4: Implement CLI commands**

Include `status`, `model-current`, `last-retraining`, `refresh-health`, `data-freshness`, `trigger-retrain`, `trigger-forecast-refresh --stock AAPL`, and `promote-model --version ...`.

- [ ] **Step 5: Test job behavior**

Run: `cd backend && pytest backend/tests/jobs/test_jobs.py -v`

Expected: jobs update status and failed retraining does not remove current promoted model.

## Task 8: Add Observability, Analytics, And Rate Limits

**Files:**

- Create: `backend/app/observability.py`
- Create: `backend/app/analytics.py`
- Create: `infra/otel-collector-config.yaml`
- Create: `backend/tests/api/test_rate_limits.py`

- [ ] **Step 1: Add OpenTelemetry instrumentation**

Instrument FastAPI requests, Celery jobs, provider calls, and model refresh/retraining operations.

- [ ] **Step 2: Add minimal anonymous analytics endpoint**

Accept product events without user identity. Retain raw events for 90 days.

- [ ] **Step 3: Add protective rate limits**

Protect repeated stock detail, news refresh, and provider-expensive requests.

- [ ] **Step 4: Test rate limits**

Run: `cd backend && pytest backend/tests/api/test_rate_limits.py -v`

Expected: excessive repeated requests receive a clear throttling response.

## Task 9: Build Expo Mobile Screens

**Files:**

- Create: `mobile/src/screens/StockSearchScreen.tsx`
- Create: `mobile/src/screens/StockDetailScreen.tsx`
- Create: `mobile/src/components/PredictionCard.tsx`
- Create: `mobile/src/components/ForecastGraph.tsx`
- Create: `mobile/src/components/CompareWithSheet.tsx`
- Create: `mobile/src/components/CompanyNewsList.tsx`
- Create: `mobile/src/components/StockSummary.tsx`
- Create: `mobile/src/storage/localPreferences.ts`

- [ ] **Step 1: Generate TypeScript API client**

Generate client/types from FastAPI OpenAPI into `mobile/src/api/generated/`.

- [ ] **Step 2: Implement launch behavior**

Open cached last primary Stock and cached Forecast Horizon when available; otherwise open Stock Search.

- [ ] **Step 3: Implement Stock Search**

Search supported stocks only and select one primary Stock.

- [ ] **Step 4: Implement Stock Detail**

Display header, freshness labels, disclaimer, horizon selector, prediction card, forecast graph, Stock Summary, and Company News.

- [ ] **Step 5: Implement comparison flow**

Use a bottom sheet to add up to two comparison Stocks, show compact prediction cards, normalized comparison graph, active-stock selector, and remove actions.

- [ ] **Step 6: Implement local preferences**

Persist primary Stock, Forecast Horizon, graph type, and cached stock detail. Do not persist comparison Stocks or hidden graph state.

- [ ] **Step 7: Verify mobile checks**

Run: `cd mobile && npm test`

Run: `cd mobile && npm run typecheck`

Expected: tests and TypeScript checks pass.

## Task 10: Add Legal, Privacy, And Settings/About Screen

**Files:**

- Create: `docs/legal/privacy-policy.md`
- Create: `docs/legal/terms-disclaimer.md`
- Create: `mobile/src/screens/SettingsScreen.tsx`

- [ ] **Step 1: Draft legal documents**

Include privacy policy, terms/disclaimer, and financial-information disclaimer.

- [ ] **Step 2: Add minimal settings/about screen**

Expose legal/privacy links, app version, disclaimer, and clear local cache action.

- [ ] **Step 3: Test clear cache**

Verify clearing cache removes primary Stock, Forecast Horizon, graph type preference, and cached stock detail.

## Task 11: Add CI

**Files:**

- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Add backend checks**

Run backend tests, lint, and type checks.

- [ ] **Step 2: Add mobile checks**

Run TypeScript checks, lint, and tests.

- [ ] **Step 3: Add Docker checks**

Validate Docker Compose config and build backend images.

- [ ] **Step 4: Add OpenAPI client check**

Fail CI if generated TypeScript client is stale compared to backend OpenAPI.

## Acceptance Criteria

- Local Docker Compose starts backend, PostgreSQL, Redis, Celery worker, scheduler, and observability services.
- Expo app starts locally outside Docker and can call the backend.
- User can search/select a supported primary Stock.
- App opens the cached last primary Stock and horizon on relaunch.
- Stock Detail shows prediction, forecast graph, summary, news, freshness labels, and disclaimer.
- User can compare with up to two supported Stocks.
- Comparison uses one shared Forecast Horizon and one shared graph type.
- Each selected Stock has its own Stock Prediction.
- Forecast graph supports line and candlestick views.
- Forecasts are grounded in Market Snapshots and External Factors, not prior Predictions.
- News refreshes on access.
- Forecast refresh jobs run for tracked/requested Stocks.
- Weekly retraining creates candidate models and promotes only after validation.
- OpenAI summaries fall back to deterministic summaries when unavailable.
- No buy/sell/hold recommendations appear in API or UI.
- No accounts, watchlists, monetization, or notifications exist in the prototype.
