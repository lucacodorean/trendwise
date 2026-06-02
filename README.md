# Trendwise

Trendwise is a learning-focused stock forecasting prototype. The idea is to build a mobile-native app that combines market data, forecast graphs, analytical prediction signals, company news, summaries, and key factors into one coherent stock analysis experience.

This project is not a trading advisor. It does not provide buy, sell, or hold recommendations, and it is not intended to be used as financial advice.

## Project Idea

Trendwise explores how a stock analysis product can present future-looking estimates while staying clear about uncertainty, data freshness, and risk. A user selects a supported US-listed common stock, chooses a forecast horizon, and sees:

- A stock forecast graph with historical context and projected price behavior
- A stock prediction signal such as bullish, bearish, or neutral
- Confidence, expected change, and risk level
- Key factors that explain the signal
- A concise stock summary grounded in market data and company news
- Relevant company news
- Optional comparison with up to two other stocks

Forecasts and predictions are meant to be analytical outputs, not recommendations. Historical data, market snapshots, external factors, and model logic should remain distinct so the system can be audited and improved over time.

## Learning Goals

This repository is primarily a portfolio and learning project. The goal is to practice building a realistic full-stack, data-driven application with clear product boundaries and production-inspired engineering practices.

The main learning goals are:

- Design a modular Python backend with FastAPI
- Model a financial-analysis domain without implying personalized investment advice
- Build provider adapters for market data, company news, and generated summaries
- Store market snapshots, forecasts, and prediction runs in a durable database
- Create an ML-oriented forecasting pipeline with validation and retraining paths
- Use background jobs for scheduled refreshes and data ingestion
- Generate a typed frontend API client from the backend OpenAPI contract
- Build a native mobile frontend with Expo React Native and TypeScript
- Practice local infrastructure with Docker Compose, PostgreSQL, Redis, and Celery
- Add observability, tests, CI, and documentation from the start

## Planned Architecture

Trendwise is planned as a monorepo with these main areas:

- `backend/`: FastAPI app, domain logic, provider adapters, storage, ML pipeline, background jobs, admin tooling, and tests
- `mobile/`: Expo React Native app, screens, components, generated API client, and local preferences/cache
- `infra/`: Docker Compose services and local infrastructure configuration
- `docs/`: product decisions, architecture decision records, and implementation plans
- `.github/workflows/`: CI checks for backend, frontend, and generated contracts

The backend owns the domain rules and exposes stock-detail payloads optimized for the mobile app. The mobile app consumes generated TypeScript types from the backend OpenAPI schema to reduce contract drift.

## Local Prototype Setup

Copy `.env.example` to `.env` for local overrides. Keep real provider keys and local secrets out of git.

Expo runs locally on the Mac while backend services run in Docker. The Expo mobile app reads `EXPO_PUBLIC_API_BASE_URL` for backend requests. Set `EXPO_PUBLIC_API_BASE_URL` in `.env` before `./scripts/dev up`; for physical devices, use your dev machine LAN URL, for example `http://192.168.x.x:8000`.

Use Docker Compose for local development. The repo-owned helper script wraps the standard commands.

Start the full local stack:

```bash
./scripts/dev up
```

Start a LAN Expo session with local Expo and Docker backend services:

```bash
./scripts/dev expo
```

Run backend tests in Docker:

```bash
./scripts/dev test
```

Run mobile TypeScript checks in Docker:

```bash
./scripts/dev typecheck
```

Refresh Docker images and mobile dependencies after package changes:

```bash
./scripts/dev update
```

The Compose stack starts the FastAPI backend, PostgreSQL, Redis, Celery worker, Celery scheduler, OpenTelemetry Collector, and Jaeger. Expo runs locally through `./scripts/dev expo`. The backend health endpoint is available at `http://localhost:8000/health`.

## Prototype Scope

The initial prototype is intentionally constrained:

- Free to use
- No accounts
- No subscriptions or ads
- No watchlists
- No notifications
- English-only
- Supported-stock search instead of unrestricted ticker input
- US-listed common stocks only
- No ETFs, OTC securities, funds, preferred shares, warrants, delisted symbols, or non-US exchanges

These constraints keep the project focused on the core learning goal: building an auditable stock forecasting and analysis system rather than a trading platform.

## Forecast Horizons

The planned canonical forecast horizons are:

- `30m`
- `1d`
- `5d`
- `7d`
- `1mo`
- `6mo`
- `1y`

Each horizon should update the forecast graph, prediction signal, summary, news window, and external-factor weighting together.

## Roadmap

Planned implementation milestones:

1. Bootstrap the monorepo, backend health endpoint, frontend shell, and local infrastructure.
2. Define core domain models for stocks, forecast horizons, forecasts, predictions, risk, and comparison rules.
3. Add persistence with PostgreSQL migrations and repository tests.
4. Implement provider adapters for market data, news, and grounded summaries.
5. Build the first ML forecasting and prediction pipeline.
6. Expose stock search and stock detail APIs.
7. Add background jobs for refreshes and retraining.
8. Generate the TypeScript API client from OpenAPI.
9. Build the Expo mobile screens for search, stock detail, graphing, summaries, news, and comparison.
10. Add CI, observability, legal/privacy placeholders, and public documentation.

## Status

Trendwise is currently in prototype planning. Product decisions, architecture decisions, and implementation tasks live in `docs/`.

## Disclaimer

Trendwise is an educational software project. Any forecasts, predictions, summaries, or risk labels produced by the app are informational estimates only. They are not financial advice, investment advice, or recommendations to buy, sell, or hold any security.
