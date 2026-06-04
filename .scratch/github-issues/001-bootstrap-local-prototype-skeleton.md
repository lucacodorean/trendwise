---
title: Bootstrap local prototype skeleton
labels: ready-for-agent
---

## What to build

Create the first runnable Trendwise prototype skeleton: a monorepo with a FastAPI backend health check, Expo React Native TypeScript shell, Docker Compose local infrastructure, environment documentation, and the first smoke checks. This slice should make the repo executable locally and establish the backend-owned OpenAPI contract path.

This implementation should be grounded in the accepted project context:

- ADR 0001 requires a Python FastAPI backend, an Expo React Native TypeScript frontend, and backend-owned OpenAPI as the API contract source.
- ADR 0002 requires a modular Python backend codebase, PostgreSQL as durable storage, Celery for background jobs, Redis as Celery infrastructure, and local Docker Compose infrastructure.
- The PRD describes Trendwise as an off-production, local-first prototype where Docker Compose starts backend infrastructure while Expo development runs separately from Compose.
- The PRD also requires local secrets to stay in uncommitted `.env` files, with `.env.example` documenting required configuration without committing secrets.

## Acceptance criteria

- [ ] The repository contains `backend/`, `mobile/`, `infra/`, `docs/`, and `.github/workflows/`-ready structure consistent with the product docs and ADRs.
- [ ] FastAPI exposes `/health` returning a successful service status and has a passing backend health test.
- [ ] Docker Compose defines backend, PostgreSQL, Redis, Celery worker, scheduler, OpenTelemetry Collector, and optional trace viewer services.
- [ ] Expo TypeScript app skeleton exists under `mobile/` and is intended to run separately from Docker Compose.
- [ ] `.env.example` documents required local configuration without committing secrets.
- [ ] The README or local setup notes explain how to run the backend health check, Docker Compose stack, and Expo app separately.

## Blocked by

None - can start immediately
