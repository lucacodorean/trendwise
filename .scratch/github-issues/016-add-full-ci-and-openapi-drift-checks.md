---
title: Add full CI and OpenAPI drift checks
labels: ready-for-agent
---

## What to build

Add GitHub Actions CI covering backend checks, mobile checks, Docker checks, and generated OpenAPI client drift. CI should make contract drift visible and keep the prototype runnable across backend and mobile changes.

## Acceptance criteria

- [ ] GitHub Actions runs backend tests, lint, and type checks.
- [ ] GitHub Actions runs mobile TypeScript checks, lint, and tests.
- [ ] GitHub Actions validates Docker Compose config and backend image build.
- [ ] CI fails when generated TypeScript API client artifacts are stale relative to FastAPI OpenAPI.
- [ ] CI is documented enough for AFK agents to run equivalent checks locally.

## Blocked by

- #1
- #3
- #8
