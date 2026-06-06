import re
from pathlib import Path


def assert_create_table_call_exists(migration: str, table_name: str) -> None:
    assert re.search(rf'op\.create_table\(\s*"{table_name}"', migration)


def create_table_start(migration: str, table_name: str) -> int:
    match = re.search(rf'op\.create_table\(\s*"{table_name}"', migration)
    assert match is not None
    return match.start()


def migration_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "migrations"
        / "versions"
        / "0001_initial_persistence_schema.py"
    )


def test_initial_migration_is_valid_python() -> None:
    path = migration_path()
    compile(path.read_text(), str(path), "exec")


def test_initial_migration_defines_required_persistence_tables() -> None:
    migration = migration_path().read_text()

    for table_name in (
        "stocks",
        "market_snapshots",
        "forecast_runs",
        "prediction_runs",
        "forecast_source_market_snapshots",
        "company_news",
        "external_factors",
        "forecast_source_company_news",
        "forecast_source_external_factors",
        "model_versions",
        "job_statuses",
        "anonymous_analytics_events",
    ):
        assert_create_table_call_exists(migration, table_name)

    forecast_source_start = create_table_start(migration, "forecast_source_market_snapshots")
    company_news_start = create_table_start(migration, "company_news")
    forecast_source_section = migration[forecast_source_start:company_news_start]
    assert "market_snapshots.id" in forecast_source_section
    assert "prediction_runs.id" not in forecast_source_section

    company_news_source_start = create_table_start(migration, "forecast_source_company_news")
    external_factor_source_start = create_table_start(migration, "forecast_source_external_factors")
    external_factor_source_end = create_table_start(migration, "forecast_line_points")
    company_news_source_section = migration[company_news_source_start:external_factor_source_start]
    external_factor_source_section = migration[external_factor_source_start:external_factor_source_end]
    assert "forecast_runs.id" in company_news_source_section
    assert "company_news.id" in company_news_source_section
    assert "prediction_runs.id" not in company_news_source_section
    assert "forecast_runs.id" in external_factor_source_section
    assert "external_factors.id" in external_factor_source_section
    assert "prediction_runs.id" not in external_factor_source_section


def test_initial_migration_defines_seed_upsert_uniqueness_constraints() -> None:
    migration = migration_path().read_text()

    assert re.search(
        r'sa\.UniqueConstraint\(\s*"stock_id",\s*"provider",\s*"observed_at",\s*'
        r'name="uq_market_snapshots_stock_provider_observed"',
        migration,
    )


def test_initial_migration_indexes_latest_prediction_lookup() -> None:
    migration = migration_path().read_text()

    assert '"ix_prediction_runs_stock_horizon_generated"' in migration
    assert re.search(
        r'sa\.UniqueConstraint\(\s*"stock_id",\s*"horizon",\s*"generated_at",\s*'
        r'name="uq_forecast_runs_stock_horizon_generated"',
        migration,
    )
    assert re.search(
        r'sa\.UniqueConstraint\(\s*"stock_id",\s*"horizon",\s*"forecast_run_id",\s*'
        r'"generated_at",\s*name="uq_prediction_runs_stock_horizon_forecast_generated"',
        migration,
    )


def test_initial_migration_defines_detailed_forecast_and_prediction_tables() -> None:
    migration = migration_path().read_text()

    for table_name in (
        "forecast_line_points",
        "forecast_candlesticks",
        "prediction_key_factors",
    ):
        assert_create_table_call_exists(migration, table_name)

    line_points_start = create_table_start(migration, "forecast_line_points")
    candlesticks_start = create_table_start(migration, "forecast_candlesticks")
    key_factors_start = create_table_start(migration, "prediction_key_factors")
    job_statuses_start = create_table_start(migration, "job_statuses")

    line_points_section = migration[line_points_start:candlesticks_start]
    candlesticks_section = migration[candlesticks_start:key_factors_start]
    key_factors_section = migration[key_factors_start:job_statuses_start]

    assert "forecast_runs.id" in line_points_section
    for column_name in ("sequence", "timestamp", "expected_value", "lower_bound", "upper_bound"):
        assert f'"{column_name}"' in line_points_section
    assert re.search(
        r'sa\.UniqueConstraint\(\s*"forecast_run_id",\s*"sequence",\s*'
        r'name="uq_forecast_line_points_run_sequence"',
        line_points_section,
    )

    assert "forecast_runs.id" in candlesticks_section
    for column_name in (
        "sequence",
        "timestamp",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
    ):
        assert f'"{column_name}"' in candlesticks_section
    assert re.search(
        r'sa\.UniqueConstraint\(\s*"forecast_run_id",\s*"sequence",\s*'
        r'name="uq_forecast_candlesticks_run_sequence"',
        candlesticks_section,
    )

    assert "prediction_runs.id" in key_factors_section
    for column_name in (
        "sequence",
        "factor_type",
        "source_reference_type",
        "source_id",
        "label",
        "numeric_value",
        "rationale",
        "polarity",
        "weight",
    ):
        assert f'"{column_name}"' in key_factors_section
    assert 'name="ck_prediction_key_factors_polarity"' in key_factors_section
    assert re.search(
        r'sa\.UniqueConstraint\(\s*"prediction_run_id",\s*"sequence",\s*'
        r'name="uq_prediction_key_factors_run_sequence"',
        key_factors_section,
    )


def test_initial_migration_drops_detailed_tables_before_run_tables() -> None:
    migration = migration_path().read_text()
    downgrade_start = migration.index("def downgrade()")
    downgrade_section = migration[downgrade_start:]

    detailed_table_positions = [
        downgrade_section.index(f'"{table_name}"')
        for table_name in (
            "prediction_key_factors",
            "forecast_candlesticks",
            "forecast_line_points",
        )
    ]
    prediction_runs_position = downgrade_section.index('"prediction_runs"')
    forecast_runs_position = downgrade_section.index('"forecast_runs"')

    assert all(position < prediction_runs_position for position in detailed_table_positions)
    assert all(position < forecast_runs_position for position in detailed_table_positions)
