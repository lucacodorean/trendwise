# Database Seeder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable backend database seeding system and the first supported Stocks seeder, runnable through Docker.

**Architecture:** Create `backend/app/database/` as the database package with connection management, abstract seeder protocol, concrete seeders, and a registry runner. The first seeder creates and upserts supported US-listed common Stocks from a committed CSV. `scripts/dev seed-db` runs the seeder through a one-shot Docker Compose service.

**Tech Stack:** Python, psycopg, PostgreSQL, Docker Compose, pytest.

---

## File Structure

- Create `backend/app/database/__init__.py`: package marker.
- Create `backend/app/database/connection.py`: opens a PostgreSQL connection from `DATABASE_URL`.
- Create `backend/app/database/seed.py`: CLI entrypoint that runs all seeders.
- Create `backend/app/database/seeders/__init__.py`: exports seeder registry.
- Create `backend/app/database/seeders/base.py`: abstract `DatabaseSeeder` protocol.
- Create `backend/app/database/seeders/runner.py`: runs seeders in order.
- Create `backend/app/database/seeders/supported_stocks.py`: creates/upserts `supported_stocks` rows from CSV.
- Create `backend/app/database/seed_data/supported_stocks.csv`: broad starter universe of supported US-listed common Stocks.
- Modify `backend/pyproject.toml`: add `psycopg[binary]`.
- Modify `docker-compose.yml`: add `seed-db` tools-profile service.
- Modify `scripts/dev`: add `seed-db` command.
- Create `backend/tests/database/test_seeders.py`: verifies runner order and supported Stocks SQL behavior through fake connection/cursor boundaries.
- Modify `backend/tests/test_dev_script.py`: verifies `seed-db` command is wired.
- Modify `backend/tests/test_local_infrastructure.py`: verifies Compose service is wired.

## Task 1: Abstract Seeder Runner

**Files:**
- Create: `backend/tests/database/test_seeders.py`
- Create: `backend/app/database/seeders/base.py`
- Create: `backend/app/database/seeders/runner.py`

- [ ] **Step 1: Write a failing test for ordered seeder execution**

Test that `run_seeders(connection, [first, second])` calls seeders in order with the same connection.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/database/test_seeders.py -v`

Expected: FAIL because `app.database.seeders.runner` does not exist.

- [ ] **Step 3: Implement protocol and runner**

Add `DatabaseSeeder` protocol and `run_seeders`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/database/test_seeders.py -v`

Expected: PASS.

## Task 2: Supported Stocks Seeder

**Files:**
- Modify: `backend/tests/database/test_seeders.py`
- Create: `backend/app/database/seeders/supported_stocks.py`
- Create: `backend/app/database/seed_data/supported_stocks.csv`

- [ ] **Step 1: Write a failing test for supported Stocks seeding**

Test that `SupportedStocksSeeder` creates `supported_stocks`, reads CSV rows, and executes upserts for supported rows.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/database/test_seeders.py -v`

Expected: FAIL because `SupportedStocksSeeder` does not exist.

- [ ] **Step 3: Implement the seeder and seed CSV**

Create the table idempotently and upsert CSV rows by ticker.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/database/test_seeders.py -v`

Expected: PASS.

## Task 3: Docker Script Wiring

**Files:**
- Modify: `backend/tests/test_dev_script.py`
- Modify: `backend/tests/test_local_infrastructure.py`
- Modify: `backend/pyproject.toml`
- Modify: `docker-compose.yml`
- Modify: `scripts/dev`

- [ ] **Step 1: Write failing tests for `seed-db` script and Compose service**

Assert `scripts/dev` contains `seed-db` and `docker compose run --rm seed-db`. Assert Compose contains a `seed-db` service under `tools` profile with command `python -m app.database.seed`.

- [ ] **Step 2: Run focused tests to verify failure**

Run: `cd backend && python3 -m pytest tests/test_dev_script.py tests/test_local_infrastructure.py -v`

Expected: FAIL because `seed-db` is not wired.

- [ ] **Step 3: Add dependency, Compose service, and script command**

Add `psycopg[binary]`, `seed-db` Compose service, and `scripts/dev seed-db`.

- [ ] **Step 4: Run focused tests to verify pass**

Run: `cd backend && python3 -m pytest tests/test_dev_script.py tests/test_local_infrastructure.py -v`

Expected: PASS.

## Task 4: Verification

**Files:**
- No source changes unless verification exposes a defect.

- [ ] **Step 1: Run Docker backend tests**

Run: `./scripts/dev test`

Expected: all tests pass.

- [ ] **Step 2: Validate Compose config**

Run: `./scripts/dev config`

Expected: config includes `seed-db` only under `tools` profile.

- [ ] **Step 3: Run seed command**

Run: `./scripts/dev seed-db`

Expected: supported Stocks table is created/upserted without errors.

## Self-Review

- Spec coverage: covers abstract seeder collection, supported Stocks database seeding, and Docker script execution.
- Placeholder scan: no placeholders remain.
- Type consistency: `DatabaseSeeder`, `SupportedStocksSeeder`, `run_seeders`, and `seed-db` names are consistent.
