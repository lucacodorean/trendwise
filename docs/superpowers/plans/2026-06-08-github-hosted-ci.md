# GitHub Hosted CI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a small GitHub Actions CI workflow that runs backend Python tests and mobile TypeScript checks on GitHub-hosted runners.

**Architecture:** `.github/workflows/ci.yml` orchestrates CI jobs. Each job delegates its setup and command sequence to a focused local composite action under `.github/actions/` so backend and mobile checks can evolve independently. Backend dev dependencies include the real `httpx` package required by FastAPI/Starlette `TestClient` in a clean CI environment.

**Tech Stack:** GitHub Actions, `actions/setup-python@v5`, `actions/setup-node@v4`, Python 3.11, Node 22, pytest, httpx, npm, TypeScript.

---

### Task 1: Create the CI Orchestrator

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Define CI triggers and jobs**

```yaml
name: CI

on:
  pull_request:
  push:
    branches:
      - master

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/backend-tests

  mobile-typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/mobile-typecheck
```

- [ ] **Step 2: Validate the YAML path references**

Run: `git diff -- .github/workflows/ci.yml`

Expected: `ci.yml` references `.github/actions/backend-tests` and `.github/actions/mobile-typecheck`.

### Task 2: Create the Backend Composite Action

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `.github/actions/backend-tests/action.yml`
- Delete: `.github/workflows/actions/backend-tests.yml`

- [ ] **Step 1: Ensure backend test dependencies match FastAPI TestClient**

```toml
[project.optional-dependencies]
dev = [
    "httpx>=0.27,<1",
    "pytest>=8,<9",
]
```

- [ ] **Step 2: Add the backend action**

```yaml
name: Backend Tests
description: Set up Python and run backend tests

runs:
  using: composite
  steps:
    - uses: actions/setup-python@v5
      with:
        python-version: "3.11"

    - name: Install backend dependencies
      shell: bash
      working-directory: backend
      run: python -m pip install ".[dev]"

    - name: Run backend tests
      shell: bash
      working-directory: backend
      run: python -m pytest -v
```

- [ ] **Step 3: Remove the misplaced workflow fragment**

Run: `git diff -- .github/actions/backend-tests/action.yml .github/workflows/actions/backend-tests.yml`

Expected: the backend action lives at `.github/actions/backend-tests/action.yml`; the old empty fragment is deleted.

### Task 3: Create the Mobile Typecheck Composite Action

**Files:**
- Create: `.github/actions/mobile-typecheck/action.yml`
- Delete: `.github/workflows/actions/mobile-tests.yml`

- [ ] **Step 1: Add the mobile typecheck action**

```yaml
name: Mobile Typecheck
description: Set up Node and run mobile TypeScript checks

runs:
  using: composite
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: "22"
        cache: npm
        cache-dependency-path: mobile/package-lock.json

    - name: Install mobile dependencies
      shell: bash
      working-directory: mobile
      run: npm ci

    - name: Run mobile typecheck
      shell: bash
      working-directory: mobile
      run: npm run typecheck
```

- [ ] **Step 2: Remove the misplaced workflow fragment**

Run: `git diff -- .github/actions/mobile-typecheck/action.yml .github/workflows/actions/mobile-tests.yml`

Expected: the mobile action lives at `.github/actions/mobile-typecheck/action.yml`; the old empty fragment is deleted.

### Task 4: Verify Locally

**Files:**
- Read: `.github/workflows/ci.yml`
- Read: `.github/actions/backend-tests/action.yml`
- Read: `.github/actions/mobile-typecheck/action.yml`

- [ ] **Step 1: Run backend tests with the same command as CI**

Run: `python -m pip install ".[dev]" && python -m pytest -v` from `backend`.

Expected: pytest collects and runs the backend suite.

- [ ] **Step 2: Run mobile typecheck with the same command as CI**

Run: `npm ci && npm run typecheck` from `mobile`.

Expected: TypeScript exits successfully or reports actionable type errors.

- [ ] **Step 3: Inspect git diff**

Run: `git diff -- .github docs/superpowers/plans/2026-06-08-github-hosted-ci.md`

Expected: only CI workflow/action files and this plan are changed.

---

## Self-Review

- Spec coverage: The plan covers GitHub-hosted backend tests and mobile typecheck, with `ci.yml` connecting separate files. It also covers the backend dev dependency needed for FastAPI/Starlette `TestClient` in clean CI environments.
- Placeholder scan: No placeholders remain.
- Type consistency: File paths and local action names match between `ci.yml` and action directories.
