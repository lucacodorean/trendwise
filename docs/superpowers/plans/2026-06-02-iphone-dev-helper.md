# iPhone Dev Helper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `./scripts/dev expo` to make LAN Expo QA startup easier.

**Architecture:** Extend the existing Docker-first `scripts/dev` helper with a small LAN IP detector and an `iphone` command. The command starts the Compose stack with `EXPO_PUBLIC_API_BASE_URL` set to the Mac LAN backend URL, runs the existing seed-db service, and prints the Expo URL to open in Expo Go.

**Tech Stack:** POSIX shell, Docker Compose, pytest file-content/script tests.

---

### Task 1: Add iPhone Helper Command

**Files:**
- Modify: `scripts/dev`
- Modify: `backend/tests/test_dev_script.py`

- [ ] **Step 1: Write failing tests**

Add tests asserting `scripts/dev` exposes an `iphone` command, detects LAN IP with `ipconfig getifaddr en0`/`en1`, starts Compose with `EXPO_PUBLIC_API_BASE_URL=http://$LAN_IP:8000`, runs `seed-db`, and prints `exp://$LAN_IP:8081` plus `docker compose down`.

- [ ] **Step 2: Verify tests fail**

Run `./scripts/dev test`. Expected: tests fail because `iphone` is not implemented.

- [ ] **Step 3: Implement minimal shell command**

Add `detect_lan_ip` and an `iphone)` case branch. The branch should fail with a clear message when no LAN IP can be detected.

- [ ] **Step 4: Verify tests pass**

Run `./scripts/dev test`. Expected: all backend tests pass.

## Self Review

- Spec coverage: covers auto LAN IP detection, Compose startup, seeding, Expo URL printing, and stop instructions.
- Placeholder scan: no placeholders.
- Type consistency: command name is consistently `iphone`.
