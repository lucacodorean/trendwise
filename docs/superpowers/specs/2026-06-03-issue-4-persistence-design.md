# Issue 4 Persistence Design

## Goal

Add durable PostgreSQL persistence for observed Market Snapshots and computed Forecast Runs and Prediction Runs, while preserving the domain boundary that forecasts are grounded in observed data and not prior predictions.

This design implements the storage foundation for issue #4. It does not implement provider ingestion, forecast generation, analytics ingestion endpoints, or background job workers.

## Architecture

Use Alembic for database schema migrations and keep repository access aligned with the existing backend style: explicit SQL through `psycopg` connections. For issue #4, "models" means durable PostgreSQL schema models represented by migrations and repository row types, not SQLAlchemy ORM classes.

The storage layer will live under `backend/app/storage/` and expose repository methods for writing and reading durable domain records. Alembic migrations are the only place that creates or changes durable tables. Seeders should assume migrations have already run and should only insert or upsert seed records into existing tables.

Service and API layers should not fetch durable records with direct database access. If existing service or route code needs database-backed Stock, Market Snapshot, Forecast Run, or Prediction Run data, it should depend on repository interfaces and call repository methods. This keeps query details contained in the storage/repository layer and keeps service code focused on domain flow, validation, and response assembly.

Expose migration execution through a repo-owned command, such as `./scripts/dev migrate-db`, so local setup does not require contributors to remember Alembic internals.

The existing database seeders should be updated as part of this work. Their `CREATE TABLE IF NOT EXISTS ...` statements should move into migrations. Seeder classes should focus on transforming committed seed data into persisted rows in migrated tables.

## Schema

The initial Alembic migration creates these tables:

- `stocks`: canonical supported Stock identity, including ticker, company name, exchange, instrument type, region, support flag, and search text.
- `market_snapshots`: observed provider market data for a Stock at a specific observation time.
- `forecast_runs`: computed Stock Forecast runs for a Stock and Forecast Horizon.
- `prediction_runs`: computed Stock Prediction runs for a Stock and Forecast Horizon.
- `company_news`: provider news records associated with a Stock.
- `external_factors`: non-price-market inputs that may influence forecasts or predictions.
- `model_versions`: metadata for promoted or candidate model versions.
- `job_statuses`: durable status records for refresh, ingestion, training, and operational jobs.
- `anonymous_analytics_events`: internal anonymous product analytics events.

Observed source data and computed analytical output remain separate:

- Observed source data: `market_snapshots`, `company_news`, `external_factors`.
- Computed output: `forecast_runs`, `prediction_runs`.

`forecast_runs` and `prediction_runs` link to `stocks`, Forecast Horizon, generated timestamps, optional `model_versions`, and source input references where applicable. Forecast source references can include Market Snapshot, Company News, and External Factor IDs. Forecast source references must not include prior Prediction Run IDs.

## Data Flow

Provider and job code will eventually write observed inputs first. Forecast generation will read eligible observed inputs and persist a Forecast Run. Prediction generation may derive from a Forecast Run and other structured signals, then persist a Prediction Run.

The first repository seam will support this round trip:

- Upsert or insert one Stock.
- Store one Market Snapshot for that Stock.
- Store one Forecast Run for the same Stock and Forecast Horizon, linked to the Market Snapshot as source evidence.
- Store one Prediction Run for the same Stock and Forecast Horizon, optionally linked to the Forecast Run.
- Retrieve the records with relationships intact.

Any existing service path that reads from the affected persistence tables should be checked during implementation. If it currently performs SQL directly, move that query behind a repository method and inject or construct the repository at the boundary already used by the route or service.

## Retention

The schema supports historical retention by using append-only run/snapshot tables with generated or observed timestamps rather than overwriting the latest value. Forecast Runs and Market Snapshots can therefore be retained for long-horizon evaluation where provider licensing permits.

Raw anonymous analytics events include a timestamp so a future cleanup job can enforce the 90-day raw-event retention policy from the product docs.

## Error Handling

Repositories should raise database errors directly for constraint failures and connectivity problems. Callers can translate those errors at API or job boundaries when user-facing behavior exists.

Migration commands should fail fast if `DATABASE_URL` is missing or PostgreSQL is unavailable.

## Testing

Add repository tests under `backend/tests/storage/` that exercise the persistence seam using PostgreSQL. The key acceptance test stores and retrieves a Market Snapshot, Forecast Run, and Prediction Run linked to the same Stock and Forecast Horizon.

Add migration-focused tests or infrastructure assertions that verify Alembic configuration exists and the initial migration defines the required tables.

Add script/Compose tests that verify the migration command is wired through the Docker-first workflow.

Update seeder tests so they verify insert/upsert behavior only. They should no longer expect seeders to execute table-creation SQL.

Update service or route tests where needed to verify service code talks to repositories rather than direct database details. Repository tests should cover SQL behavior; service tests should cover orchestration and response behavior.

Existing stock search/detail tests should continue to pass. If current `supported_stocks` seed behavior remains necessary during the transition, compatibility should be handled intentionally rather than by introducing a second durable schema.

## Implementation Boundaries

In scope:

- Alembic setup.
- Initial PostgreSQL schema migration.
- Storage repositories for the first round trip.
- Existing seeder updates so seeders rely on migrated tables instead of creating tables.
- Service/API layer updates where existing code should fetch through repositories instead of direct database access.
- Tests for schema presence and repository persistence.

Out of scope:

- Provider adapters.
- Forecast or Prediction model execution.
- Analytics ingestion API.
- Job orchestration beyond durable `job_statuses` schema.
- Admin tooling.
- TimescaleDB or specialized time-series storage.

## Self-Review

- Placeholder scan: no placeholders remain.
- Internal consistency: Alembic owns schema evolution; repositories and seeders use explicit SQL through `psycopg` against migrated tables; service/API layers call repository interfaces rather than issuing SQL directly.
- Scope check: focused on issue #4 persistence foundations only.
- Ambiguity check: Forecast Runs may reference observed source inputs, but not prior Prediction Runs as evidence.
