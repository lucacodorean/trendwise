# Local Expo Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run Expo locally on the Mac for iPhone QA while keeping backend infrastructure in Docker.

**Architecture:** Remove the long-running `mobile` Compose service from the default stack. Keep Docker tool services for mobile typecheck and OpenAPI generation. Update `./scripts/dev expo` to start backend services in Docker, seed the database, then run local Expo from `mobile/` with the LAN backend URL.

**Tech Stack:** POSIX shell, Docker Compose, Expo CLI through `npx`, pytest script/config tests.

---

### Task 1: Move Expo Startup Local

**Files:**
- Modify: `docker-compose.yml`
- Modify: `scripts/dev`
- Modify: `README.md`
- Modify: `backend/tests/test_dev_script.py`
- Modify: `backend/tests/test_local_infrastructure.py`
- Modify: `backend/tests/test_local_setup_docs.py`

- [ ] **Step 1: Write failing tests**

Update tests so they expect no long-running `mobile` service in Compose, still expect `mobile-typecheck` and `mobile-openapi`, and expect `./scripts/dev expo` to run `npx expo start --host lan` locally from `mobile/` after starting Docker backend services and running `seed-db`.

- [ ] **Step 2: Verify tests fail**

Run `./scripts/dev test`. Expected: tests fail because Compose still has `mobile` and `iphone` still starts mobile in Docker.

- [ ] **Step 3: Implement workflow change**

Remove the `mobile` service from `docker-compose.yml`. Update `scripts/dev expo` to start backend, postgres, redis, worker, scheduler, otel-collector, and jaeger in Docker with `EXPO_PUBLIC_API_BASE_URL=http://$LAN_IP:8000`; run `seed-db`; then `cd mobile` and run `EXPO_PUBLIC_API_BASE_URL=http://$LAN_IP:8000 npx expo start --host lan`.

- [ ] **Step 4: Verify**

Run `./scripts/dev test`, `./scripts/dev typecheck`, and `./scripts/dev config`. Expected: all pass; config has no long-running `mobile` service but still has `mobile-typecheck` and `mobile-openapi`.

## Self Review

- Spec coverage: covers local Expo startup, Docker backend startup, seeding, docs, and tests.
- Placeholder scan: no placeholders.
- Type consistency: command name remains `iphone`.
