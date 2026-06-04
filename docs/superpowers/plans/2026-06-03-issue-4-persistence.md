# Issue 4 Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Alembic-managed PostgreSQL persistence for observed Market Snapshots, computed Forecast Runs, and Prediction Runs while keeping seeders and service code behind repository boundaries.

**Architecture:** Alembic owns durable table creation and schema evolution. Repositories use explicit `psycopg` SQL against migrated tables, seeders only insert or upsert seed rows, and service/API code depends on repository interfaces rather than ad hoc SQL.

**Tech Stack:** Python, FastAPI, psycopg, Alembic, PostgreSQL, Docker Compose, pytest.

---

## File Structure

- Create `backend/alembic.ini`: Alembic configuration using `DATABASE_URL` through `app.core.config.settings`.
- Create `backend/migrations/env.py`: Alembic runtime environment for online migrations.
- Create `backend/migrations/script.py.mako`: migration file template.
- Create `backend/migrations/versions/0001_initial_persistence_schema.py`: creates durable persistence tables.
- Modify `backend/pyproject.toml`: add Alembic dependency.
- Modify `docker-compose.yml`: add `migrate-db` tools-profile service.
- Modify `scripts/dev`: add `migrate-db` command and run migrations before `seed-db` during Expo startup.
- Modify `backend/tests/test_dev_script.py`: assert migration command wiring.
- Modify `backend/tests/test_local_infrastructure.py`: assert Compose migration service wiring.
- Create `backend/tests/storage/test_migrations.py`: assert Alembic files and required tables exist in migration source.
- Create `backend/app/storage/__init__.py`: package marker.
- Create `backend/app/storage/repositories.py`: repository row types and `PostgresPersistenceRepository` round-trip methods.
- Create `backend/tests/storage/test_repositories.py`: repository SQL behavior tests with fake connection/cursor.
- Modify `backend/app/database/seeders/supported_stocks.py`: remove table creation SQL and upsert into migrated `stocks` table.
- Modify `backend/app/database/seeders/stock_detail.py`: remove table creation SQL and seed migrated snapshot/run tables.
- Modify `backend/tests/database/test_seeders.py`: expect seeders to insert/upsert only, not create tables.
- Modify `backend/app/stocks/repository.py`: keep stock detail/search fetching behind repository classes and align reads with migrated table names.
- Modify `backend/tests/stocks/test_stock_detail.py`: update repository SQL expectations if table names change.

## Task 1: Alembic Configuration And Docker Command

**Files:**

- Create: `backend/alembic.ini`
- Create: `backend/migrations/env.py`
- Create: `backend/migrations/script.py.mako`
- Modify: `backend/pyproject.toml`
- Modify: `docker-compose.yml`
- Modify: `scripts/dev`
- Test: `backend/tests/test_dev_script.py`
- Test: `backend/tests/test_local_infrastructure.py`

- [ ] **Step 1: Write failing tests for migration command wiring**

Add this test to `backend/tests/test_dev_script.py`:

```python
def test_dev_script_runs_alembic_migrations_through_docker() -> None:
    script = (Path(__file__).resolve().parents[2] / "scripts" / "dev").read_text()

    assert "migrate-db" in script
    assert "docker compose build migrate-db" in script
    assert "docker compose run --rm migrate-db" in script
    assert "docker compose run --rm migrate-db" in script.split("seed-db)", 1)[1]
```

Add these assertions to `test_docker_compose_declares_required_local_services` in `backend/tests/test_local_infrastructure.py`:

```python
assert "migrate-db" in services
assert services["migrate-db"]["profiles"] == ["tools"]
assert services["migrate-db"]["command"] == "alembic upgrade head"
```

- [ ] **Step 2: Run focused tests to verify failure**

Run: `cd backend && python3 -m pytest tests/test_dev_script.py tests/test_local_infrastructure.py -v`

Expected: FAIL because `migrate-db` is not wired.

- [ ] **Step 3: Add Alembic dependency and config files**

Add this dependency to `backend/pyproject.toml`:

```toml
"alembic>=1.14,<2",
```

Create `backend/alembic.ini`:

```ini
[alembic]
script_location = migrations
prepend_sys_path = .

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

Create `backend/migrations/env.py`:

```python
from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import settings

config = context.config
target_metadata = None


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(settings.database_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Create `backend/migrations/script.py.mako`:

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from alembic import op
import sqlalchemy as sa

${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 4: Add Docker and script wiring**

Add this service to `docker-compose.yml` near `seed-db`:

```yaml
  migrate-db:
    build:
      context: ./backend
    profiles:
      - tools
    env_file: .env.example
    working_dir: /workspace/backend
    command: alembic upgrade head
    volumes:
      - .:/workspace
    depends_on:
      - postgres
```

Update `scripts/dev` help text with:

```sh
'  migrate-db Run Alembic migrations in Docker' \
```

Add this case before `seed-db)`:

```sh
  migrate-db)
    docker compose build migrate-db
    docker compose run --rm migrate-db
    ;;
```

Update the `seed-db)` branch so migrations run before seeders:

```sh
  seed-db)
    docker compose build migrate-db
    docker compose run --rm migrate-db
    docker compose build seed-db
    docker compose run --rm seed-db
    ;;
```

Update the `expo)` branch so it runs migrations before seeding:

```sh
EXPO_PUBLIC_API_BASE_URL=http://$LAN_IP:8000 docker compose run --rm migrate-db
EXPO_PUBLIC_API_BASE_URL=http://$LAN_IP:8000 docker compose run --rm seed-db
```

- [ ] **Step 5: Run focused tests to verify pass**

Run: `cd backend && python3 -m pytest tests/test_dev_script.py tests/test_local_infrastructure.py -v`

Expected: PASS.

## Task 2: Initial Persistence Migration

**Files:**

- Create: `backend/migrations/versions/0001_initial_persistence_schema.py`
- Test: `backend/tests/storage/test_migrations.py`

- [ ] **Step 1: Write failing migration source test**

Create `backend/tests/storage/test_migrations.py`:

```python
from pathlib import Path


def test_initial_migration_defines_required_persistence_tables() -> None:
    migration = (
        Path(__file__).resolve().parents[2]
        / "migrations"
        / "versions"
        / "0001_initial_persistence_schema.py"
    ).read_text()

    for table_name in (
        "stocks",
        "market_snapshots",
        "forecast_runs",
        "prediction_runs",
        "company_news",
        "external_factors",
        "model_versions",
        "job_statuses",
        "anonymous_analytics_events",
    ):
        assert f'op.create_table("{table_name}"' in migration

    forecast_source_section = migration.split(
        'op.create_table(\n        "forecast_source_market_snapshots"', 1
    )[1].split('op.create_table(\n        "company_news"', 1)[0]
    assert "market_snapshots.id" in forecast_source_section
    assert "prediction_runs.id" not in forecast_source_section
```

- [ ] **Step 2: Run test to verify failure**

Run: `cd backend && python3 -m pytest tests/storage/test_migrations.py -v`

Expected: FAIL because the migration file does not exist.

- [ ] **Step 3: Add the migration**

Create `backend/migrations/versions/0001_initial_persistence_schema.py` with `op.create_table` calls for every required table. Use these core columns and constraints:

```python
"""initial persistence schema

Revision ID: 0001_initial_persistence_schema
Revises:
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_persistence_schema"
down_revision = None
branch_labels = None
depends_on = None

HORIZON_VALUES = ("30m", "1d", "5d", "7d", "1mo", "6mo", "1y")


def upgrade() -> None:
    op.create_table(
        "stocks",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("ticker", sa.Text(), nullable=False, unique=True),
        sa.Column("company_name", sa.Text(), nullable=False),
        sa.Column("exchange", sa.Text(), nullable=False),
        sa.Column("instrument_type", sa.Text(), nullable=False),
        sa.Column("region", sa.Text(), nullable=False),
        sa.Column("is_supported", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_stocks_search_text", "stocks", ["search_text"])

    op.create_table(
        "model_versions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("artifact_uri", sa.Text(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("name", "version", name="uq_model_versions_name_version"),
    )

    op.create_table(
        "market_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("stock_id", sa.BigInteger(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("latest_price", sa.Numeric(), nullable=False),
        sa.Column("daily_change", sa.Numeric(), nullable=True),
        sa.Column("daily_change_percent", sa.Numeric(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_market_snapshots_stock_observed", "market_snapshots", ["stock_id", "observed_at"])

    op.create_table(
        "forecast_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("stock_id", sa.BigInteger(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("horizon", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("expected_price", sa.Numeric(), nullable=True),
        sa.Column("lower_bound", sa.Numeric(), nullable=True),
        sa.Column("upper_bound", sa.Numeric(), nullable=True),
        sa.Column("forecast_path", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("model_version_id", sa.BigInteger(), sa.ForeignKey("model_versions.id"), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("horizon IN " + repr(HORIZON_VALUES), name="ck_forecast_runs_horizon"),
    )
    op.create_index("ix_forecast_runs_stock_horizon_generated", "forecast_runs", ["stock_id", "horizon", "generated_at"])

    op.create_table(
        "prediction_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("stock_id", sa.BigInteger(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("horizon", sa.Text(), nullable=False),
        sa.Column("forecast_run_id", sa.BigInteger(), sa.ForeignKey("forecast_runs.id"), nullable=True),
        sa.Column("model_version_id", sa.BigInteger(), sa.ForeignKey("model_versions.id"), nullable=True),
        sa.Column("direction", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(), nullable=False),
        sa.Column("expected_change_percent", sa.Numeric(), nullable=False),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("horizon IN " + repr(HORIZON_VALUES), name="ck_prediction_runs_horizon"),
        sa.CheckConstraint("direction IN ('bullish', 'bearish', 'neutral')", name="ck_prediction_runs_direction"),
        sa.CheckConstraint("risk_level IN ('low', 'medium', 'high')", name="ck_prediction_runs_risk_level"),
    )

    op.create_table(
        "forecast_source_market_snapshots",
        sa.Column("forecast_run_id", sa.BigInteger(), sa.ForeignKey("forecast_runs.id"), primary_key=True),
        sa.Column("market_snapshot_id", sa.BigInteger(), sa.ForeignKey("market_snapshots.id"), primary_key=True),
    )

    op.create_table(
        "company_news",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("stock_id", sa.BigInteger(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )

    op.create_table(
        "external_factors",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("factor_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )

    op.create_table(
        "job_statuses",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("job_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )

    op.create_table(
        "anonymous_analytics_events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("event_name", sa.Text(), nullable=False),
        sa.Column("anonymous_id", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("properties", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )


def downgrade() -> None:
    for table_name in (
        "anonymous_analytics_events",
        "job_statuses",
        "external_factors",
        "company_news",
        "forecast_source_market_snapshots",
        "prediction_runs",
        "forecast_runs",
        "market_snapshots",
        "model_versions",
        "stocks",
    ):
        op.drop_table(table_name)
```

- [ ] **Step 4: Run migration test to verify pass**

Run: `cd backend && python3 -m pytest tests/storage/test_migrations.py -v`

Expected: PASS.

## Task 3: Seeder Schema Ownership Cleanup

**Files:**

- Modify: `backend/app/database/seeders/supported_stocks.py`
- Modify: `backend/app/database/seeders/stock_detail.py`
- Modify: `backend/tests/database/test_seeders.py`

- [ ] **Step 1: Update seeder tests to reject table creation**

In `backend/tests/database/test_seeders.py`, replace creation assertions with insert-only checks:

```python
assert all("CREATE TABLE" not in sql for sql, _ in executions)
assert any("INSERT INTO stocks" in sql for sql, _ in executions)
```

For stock detail, assert migrated tables are used:

```python
assert all("CREATE TABLE" not in sql for sql, _ in executions)
assert any("INSERT INTO market_snapshots" in sql for sql, _ in executions)
assert any("INSERT INTO forecast_runs" in sql for sql, _ in executions)
assert any("INSERT INTO prediction_runs" in sql for sql, _ in executions)
```

- [ ] **Step 2: Run seeder tests to verify failure**

Run: `cd backend && python3 -m pytest tests/database/test_seeders.py -v`

Expected: FAIL because seeders still execute `CREATE TABLE` and old table names.

- [ ] **Step 3: Update supported stocks seeder**

Change `SupportedStocksSeeder.run` to remove `CREATE TABLE` and upsert into `stocks`:

```python
cursor.execute(
    """
    INSERT INTO stocks (
        ticker,
        company_name,
        exchange,
        instrument_type,
        region,
        is_supported,
        search_text
    ) VALUES (
        %(ticker)s,
        %(company_name)s,
        %(exchange)s,
        %(instrument_type)s,
        %(region)s,
        %(is_supported)s,
        %(search_text)s
    )
    ON CONFLICT (ticker) DO UPDATE SET
        company_name = EXCLUDED.company_name,
        exchange = EXCLUDED.exchange,
        instrument_type = EXCLUDED.instrument_type,
        region = EXCLUDED.region,
        is_supported = EXCLUDED.is_supported,
        search_text = EXCLUDED.search_text
    """,
    params,
)
```

- [ ] **Step 4: Update stock detail seeder**

Change `StockDetailSeeder.run` to remove all `CREATE TABLE` statements. First fetch the migrated Stock ID:

```python
cursor.execute("SELECT id FROM stocks WHERE ticker = %(ticker)s", {"ticker": ticker})
stock_row = cursor.fetchone()
if stock_row is None:
    continue
stock_id = stock_row[0]
```

Insert market snapshots:

```python
cursor.execute(
    """
    INSERT INTO market_snapshots (
        stock_id,
        provider,
        latest_price,
        daily_change,
        daily_change_percent,
        observed_at
    ) VALUES (
        %(stock_id)s,
        %(provider)s,
        %(latest_price)s,
        %(daily_change)s,
        %(daily_change_percent)s,
        %(observed_at)s
    )
    RETURNING id
    """,
    {**market_params, "stock_id": stock_id, "provider": "seed"},
)
market_snapshot_id = cursor.fetchone()[0]
```

Insert forecast and prediction rows:

```python
cursor.execute(
    """
    INSERT INTO forecast_runs (
        stock_id,
        horizon,
        status,
        generated_at
    ) VALUES (
        %(stock_id)s,
        %(horizon)s,
        %(status)s,
        %(generated_at)s
    )
    RETURNING id
    """,
    {**forecast_params, "stock_id": stock_id},
)
forecast_run_id = cursor.fetchone()[0]

cursor.execute(
    """
    INSERT INTO forecast_source_market_snapshots (
        forecast_run_id,
        market_snapshot_id
    ) VALUES (
        %(forecast_run_id)s,
        %(market_snapshot_id)s
    )
    """,
    {
        "forecast_run_id": forecast_run_id,
        "market_snapshot_id": market_snapshot_id,
    },
)

cursor.execute(
    """
    INSERT INTO prediction_runs (
        stock_id,
        horizon,
        forecast_run_id,
        direction,
        confidence,
        expected_change_percent,
        risk_level,
        generated_at
    ) VALUES (
        %(stock_id)s,
        %(horizon)s,
        %(forecast_run_id)s,
        %(direction)s,
        %(confidence)s,
        %(expected_change_percent)s,
        %(risk_level)s,
        %(generated_at)s
    )
    """,
    {**prediction_params, "stock_id": stock_id, "forecast_run_id": forecast_run_id},
)
```

- [ ] **Step 5: Run seeder tests to verify pass**

Run: `cd backend && python3 -m pytest tests/database/test_seeders.py -v`

Expected: PASS.

## Task 4: Persistence Repository Round Trip

**Files:**

- Create: `backend/app/storage/__init__.py`
- Create: `backend/app/storage/repositories.py`
- Create: `backend/tests/storage/test_repositories.py`

- [ ] **Step 1: Write repository behavior test**

Create `backend/tests/storage/test_repositories.py` with a fake connection that records SQL and returns IDs:

```python
from datetime import datetime, timezone

from app.storage.repositories import PostgresPersistenceRepository


class RecordingCursor:
    def __init__(self) -> None:
        self.executions = []
        self.return_values = [(101,), (201,), (301,), (401,)]

    def execute(self, sql: str, params: object = None) -> None:
        self.executions.append((sql, params))

    def fetchone(self):
        return self.return_values.pop(0)

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None


class RecordingConnection:
    def __init__(self) -> None:
        self.cursor_instance = RecordingCursor()
        self.commits = 0

    def cursor(self) -> RecordingCursor:
        return self.cursor_instance

    def commit(self) -> None:
        self.commits += 1


def test_repository_stores_snapshot_forecast_and_prediction_round_trip() -> None:
    connection = RecordingConnection()
    repository = PostgresPersistenceRepository(connection)
    observed_at = datetime(2026, 6, 3, 13, 30, tzinfo=timezone.utc)
    generated_at = datetime(2026, 6, 3, 14, 0, tzinfo=timezone.utc)

    result = repository.store_snapshot_forecast_prediction(
        ticker="AAPL",
        company_name="Apple Inc.",
        exchange="NASDAQ",
        horizon="1d",
        latest_price=214.35,
        daily_change=2.62,
        daily_change_percent=1.24,
        observed_at=observed_at,
        forecast_status="unavailable",
        forecast_generated_at=generated_at,
        prediction_direction="bullish",
        prediction_confidence=0.68,
        prediction_expected_change_percent=0.8,
        prediction_risk_level="medium",
        prediction_generated_at=generated_at,
    )

    assert result == {
        "stock_id": 101,
        "market_snapshot_id": 201,
        "forecast_run_id": 301,
        "prediction_run_id": 401,
    }
    sql = "\n".join(statement for statement, _ in connection.cursor_instance.executions)
    assert "INSERT INTO stocks" in sql
    assert "INSERT INTO market_snapshots" in sql
    assert "INSERT INTO forecast_runs" in sql
    assert "INSERT INTO forecast_source_market_snapshots" in sql
    assert "INSERT INTO prediction_runs" in sql
    assert connection.commits == 1
```

- [ ] **Step 2: Run test to verify failure**

Run: `cd backend && python3 -m pytest tests/storage/test_repositories.py -v`

Expected: FAIL because `app.storage.repositories` does not exist.

- [ ] **Step 3: Implement repository**

Create `backend/app/storage/__init__.py` as an empty package marker.

Create `backend/app/storage/repositories.py` with `PostgresPersistenceRepository.store_snapshot_forecast_prediction`. Use the same insert order and SQL shapes from Task 4 Step 1, each `RETURNING id`, and return:

```python
return {
    "stock_id": stock_id,
    "market_snapshot_id": market_snapshot_id,
    "forecast_run_id": forecast_run_id,
    "prediction_run_id": prediction_run_id,
}
```

The method should commit once after all inserts succeed.

- [ ] **Step 4: Run repository test to verify pass**

Run: `cd backend && python3 -m pytest tests/storage/test_repositories.py -v`

Expected: PASS.

## Task 5: Service/Repository Read Alignment

**Files:**

- Modify: `backend/app/stocks/repository.py`
- Modify: `backend/tests/stocks/test_stock_detail.py`
- Test: `backend/tests/stocks/test_stock_search.py`

- [ ] **Step 1: Update repository tests for migrated table reads**

In `backend/tests/stocks/test_stock_detail.py`, update SQL expectations so detail repository SQL reads `stocks`, `market_snapshots`, `forecast_runs`, and `prediction_runs`. The FakeConnection row sequence can remain the same.

Add assertions:

```python
sql = "\n".join(query for query, _ in connection.cursor_instance.executed)
assert "FROM stocks" in sql
assert "FROM market_snapshots" in sql
assert "FROM forecast_runs" in sql
assert "FROM prediction_runs" in sql
assert "stock_market_details" not in sql
assert "stock_forecast_details" not in sql
assert "stock_prediction_details" not in sql
```

- [ ] **Step 2: Run stock tests to verify failure**

Run: `cd backend && python3 -m pytest tests/stocks/test_stock_detail.py tests/stocks/test_stock_search.py -v`

Expected: FAIL because repositories still read legacy tables.

- [ ] **Step 3: Update stock repositories**

In `backend/app/stocks/repository.py`, update search queries from `supported_stocks` to `stocks`.

Update detail queries:

```sql
SELECT id, ticker, company_name, exchange
FROM stocks
WHERE is_supported = TRUE
  AND ticker = %(ticker)s
```

Then use `stock_id = stock[0]` for related reads:

```sql
SELECT latest_price, daily_change, daily_change_percent, observed_at
FROM market_snapshots
WHERE stock_id = %(stock_id)s
ORDER BY observed_at DESC, id DESC
LIMIT 1
```

```sql
SELECT status, generated_at
FROM forecast_runs
WHERE stock_id = %(stock_id)s
  AND horizon = %(horizon)s
ORDER BY generated_at DESC, id DESC
LIMIT 1
```

```sql
SELECT direction, confidence, expected_change_percent, risk_level, generated_at
FROM prediction_runs
WHERE stock_id = %(stock_id)s
  AND horizon = %(horizon)s
ORDER BY generated_at DESC, id DESC
LIMIT 1
```

Return `stock[1]`, `stock[2]`, and `stock[3]` for ticker, company name, and exchange.

- [ ] **Step 4: Run stock tests to verify pass**

Run: `cd backend && python3 -m pytest tests/stocks/test_stock_detail.py tests/stocks/test_stock_search.py -v`

Expected: PASS.

## Task 6: Full Verification

**Files:**

- No source changes unless verification exposes a defect.

- [ ] **Step 1: Run backend test suite**

Run: `cd backend && python3 -m pytest -v`

Expected: PASS.

- [ ] **Step 2: Validate Compose config**

Run: `./scripts/dev config`

Expected: PASS and config includes `migrate-db` and `seed-db` under the tools profile.

- [ ] **Step 3: Run migrations and seeders through Docker**

Run: `./scripts/dev migrate-db`

Expected: Alembic applies `0001_initial_persistence_schema` successfully.

Run: `./scripts/dev seed-db`

Expected: migrations run, seed rows insert/upsert, and no seeder creates tables.

## Self-Review

- Spec coverage: covers Alembic setup, initial schema, seeder cleanup, repository persistence, service/API repository boundary, Docker workflow, and verification.
- Placeholder scan: no placeholder sections remain.
- Type consistency: table names are `stocks`, `market_snapshots`, `forecast_runs`, `prediction_runs`, `company_news`, `external_factors`, `model_versions`, `job_statuses`, and `anonymous_analytics_events` throughout.
- Commit policy: this repository session does not include commit steps because commits require an explicit user request.
