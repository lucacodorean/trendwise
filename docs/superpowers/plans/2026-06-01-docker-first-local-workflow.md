# Docker-First Local Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Docker Compose the local development interface for backend tests, mobile typechecking, mobile Expo startup, and full stack startup.

**Architecture:** Keep FastAPI and Expo as separate applications, but run both through Compose services. Add a small repo-owned script that can refresh dependencies and run `docker compose up --build` so contributors have one stable entrypoint.

**Tech Stack:** Docker Compose, FastAPI, pytest, Expo React Native, TypeScript, npm.

---

## File Structure

- Modify `docker-compose.yml`: add `backend-tests`, `mobile`, and `mobile-typecheck` services.
- Create `mobile/Dockerfile`: install mobile dependencies and run Expo commands inside Docker.
- Create `scripts/dev`: shell entrypoint for update/test/up commands.
- Modify `README.md`: replace local Python/Node startup commands with Docker-first commands.
- Modify `backend/tests/test_local_infrastructure.py`: assert required Compose services exist.
- Modify `backend/tests/test_mobile_shell.py`: assert mobile service exists and uses Docker.
- Modify `backend/tests/test_local_setup_docs.py`: assert Docker-first setup is documented.

## Task 1: Compose Services

**Files:**
- Modify: `backend/tests/test_local_infrastructure.py`
- Modify: `docker-compose.yml`
- Create: `mobile/Dockerfile`

- [ ] **Step 1: Write the failing Compose service test**

Update `backend/tests/test_local_infrastructure.py` so the required service set includes `backend-tests`, `mobile`, and `mobile-typecheck`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_local_infrastructure.py -v`

Expected: FAIL because the new Compose services are missing.

- [ ] **Step 3: Add minimal Compose services**

Add `mobile/Dockerfile`, then add `backend-tests`, `mobile`, and `mobile-typecheck` services to `docker-compose.yml`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/test_local_infrastructure.py -v`

Expected: PASS.

## Task 2: Docker-First Script

**Files:**
- Create: `scripts/dev`
- Modify: `backend/tests/test_local_setup_docs.py`

- [ ] **Step 1: Write failing script/docs assertions**

Assert README references `./scripts/dev up`, `./scripts/dev test`, and `./scripts/dev update`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_local_setup_docs.py -v`

Expected: FAIL because README does not document the script.

- [ ] **Step 3: Add script and docs**

Create `scripts/dev` with `up`, `test`, `typecheck`, and `update` commands. Update README to use those commands.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/test_local_setup_docs.py -v`

Expected: PASS.

## Task 3: Verification

**Files:**
- No code changes unless verification exposes a defect.

- [ ] **Step 1: Run all backend tests**

Run: `cd backend && python3 -m pytest -v`

Expected: all tests pass.

- [ ] **Step 2: Validate Compose config**

Run: `docker compose config`

Expected: Compose renders successfully and includes backend, backend-tests, mobile, and mobile-typecheck services.

- [ ] **Step 3: Validate script help**

Run: `./scripts/dev help`

Expected: script prints supported commands.

## Self-Review

- Spec coverage: covers Docker-first Compose services, repo-owned startup/update script, README update, and verification.
- Placeholder scan: no placeholders remain.
- Type consistency: service names are consistent across tests, Compose, docs, and script.
