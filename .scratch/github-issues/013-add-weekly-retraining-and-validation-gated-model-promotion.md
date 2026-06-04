---
title: Add weekly retraining and validation-gated model promotion
labels: ready-for-agent
---

## What to build

Implement scheduled model retraining and validation-gated promotion. Candidate models should be recorded with metadata and local filesystem artifacts, promoted only after validation passes, and never replace the current promoted model when training or validation fails.

## Acceptance criteria

- [ ] Weekly scheduled retraining creates candidate model records and local model artifacts.
- [ ] Model metadata is stored in PostgreSQL and artifacts are stored on the local filesystem volume.
- [ ] Candidate models are promoted only after validation passes.
- [ ] Failed retraining or failed validation keeps the current promoted model available.
- [ ] CLI includes current model, last retraining, trigger retraining, and promote validated model commands.
- [ ] Tests verify failed candidate models do not replace the current promoted model.
- [ ] No user-facing historical accuracy reporting is added in the prototype.

## Blocked by

- #6
- #12
