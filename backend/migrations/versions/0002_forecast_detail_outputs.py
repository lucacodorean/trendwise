"""forecast detail outputs

Revision ID: 0002_forecast_detail_outputs
Revises: 0001_initial_persistence_schema
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_forecast_detail_outputs"
down_revision = "0001_initial_persistence_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
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


def downgrade() -> None:
    for table_name in (
        "prediction_key_factors",
        "forecast_candlesticks",
        "forecast_line_points",
    ):
        op.drop_table(table_name)
