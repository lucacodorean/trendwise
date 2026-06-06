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
        sa.UniqueConstraint(
            "stock_id",
            "provider",
            "observed_at",
            name="uq_market_snapshots_stock_provider_observed",
        ),
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
        sa.UniqueConstraint(
            "stock_id",
            "horizon",
            "generated_at",
            name="uq_forecast_runs_stock_horizon_generated",
        ),
    )
    op.create_index(
        "ix_forecast_runs_stock_horizon_generated",
        "forecast_runs",
        ["stock_id", "horizon", "generated_at"],
    )

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
        sa.UniqueConstraint(
            "stock_id",
            "horizon",
            "forecast_run_id",
            "generated_at",
            name="uq_prediction_runs_stock_horizon_forecast_generated",
        ),
    )
    op.create_index(
        "ix_prediction_runs_stock_horizon_generated",
        "prediction_runs",
        ["stock_id", "horizon", "generated_at"],
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
        "forecast_source_company_news",
        sa.Column("forecast_run_id", sa.BigInteger(), sa.ForeignKey("forecast_runs.id"), primary_key=True),
        sa.Column("company_news_id", sa.BigInteger(), sa.ForeignKey("company_news.id"), primary_key=True),
    )

    op.create_table(
        "forecast_source_external_factors",
        sa.Column("forecast_run_id", sa.BigInteger(), sa.ForeignKey("forecast_runs.id"), primary_key=True),
        sa.Column("external_factor_id", sa.BigInteger(), sa.ForeignKey("external_factors.id"), primary_key=True),
    )

    op.create_table(
        "forecast_line_points",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("forecast_run_id", sa.BigInteger(), sa.ForeignKey("forecast_runs.id"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_value", sa.Numeric(), nullable=False),
        sa.Column("lower_bound", sa.Numeric(), nullable=False),
        sa.Column("upper_bound", sa.Numeric(), nullable=False),
        sa.UniqueConstraint(
            "forecast_run_id",
            "sequence",
            name="uq_forecast_line_points_run_sequence",
        ),
    )

    op.create_table(
        "forecast_candlesticks",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("forecast_run_id", sa.BigInteger(), sa.ForeignKey("forecast_runs.id"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open_price", sa.Numeric(), nullable=False),
        sa.Column("high_price", sa.Numeric(), nullable=False),
        sa.Column("low_price", sa.Numeric(), nullable=False),
        sa.Column("close_price", sa.Numeric(), nullable=False),
        sa.UniqueConstraint(
            "forecast_run_id",
            "sequence",
            name="uq_forecast_candlesticks_run_sequence",
        ),
    )

    op.create_table(
        "prediction_key_factors",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("prediction_run_id", sa.BigInteger(), sa.ForeignKey("prediction_runs.id"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("factor_type", sa.Text(), nullable=False),
        sa.Column("source_reference_type", sa.Text(), nullable=True),
        sa.Column("source_id", sa.BigInteger(), nullable=True),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("numeric_value", sa.Numeric(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("polarity", sa.Text(), nullable=False),
        sa.Column("weight", sa.Numeric(), nullable=True),
        sa.CheckConstraint(
            "polarity IN ('positive', 'negative', 'neutral')",
            name="ck_prediction_key_factors_polarity",
        ),
        sa.UniqueConstraint(
            "prediction_run_id",
            "sequence",
            name="uq_prediction_key_factors_run_sequence",
        ),
    )

    op.create_table(
        "job_statuses",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("job_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
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
        "prediction_key_factors",
        "forecast_candlesticks",
        "forecast_line_points",
        "forecast_source_external_factors",
        "forecast_source_company_news",
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
