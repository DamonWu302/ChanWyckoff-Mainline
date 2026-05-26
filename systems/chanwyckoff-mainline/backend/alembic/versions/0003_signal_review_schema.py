"""signal review schema

Revision ID: 0003_signal_review_schema
Revises: 0002_market_data_schema
Create Date: 2026-05-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_signal_review_schema"
down_revision: str | None = "0002_market_data_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "signal_review_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("signal_uid", sa.String(length=96), nullable=False),
        sa.Column("ts_code", sa.String(length=16), nullable=False),
        sa.Column("signal_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rule_state", sa.String(length=32), nullable=False),
        sa.Column("suggested_action", sa.String(length=32), nullable=False),
        sa.Column("manual_status", sa.String(length=32), nullable=False),
        sa.Column("failure_reason", sa.String(length=96), nullable=True),
        sa.Column("return_pct", sa.Numeric(12, 6), nullable=True),
        sa.Column("max_drawdown_pct", sa.Numeric(12, 6), nullable=True),
        sa.Column("holding_bars", sa.Integer(), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("signal_uid", name="uq_signal_review_records_signal_uid"),
    )
    op.create_index("ix_signal_review_records_manual_status", "signal_review_records", ["manual_status"])
    op.create_index("ix_signal_review_records_ts_code", "signal_review_records", ["ts_code"])

    op.create_table(
        "signal_review_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("manual_status", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("failure_reason", sa.String(length=96), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["record_id"], ["signal_review_records.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signal_review_events_manual_status", "signal_review_events", ["manual_status"])

    op.create_table(
        "signal_llm_reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("background_summary", sa.Text(), nullable=False),
        sa.Column("feature_summary", sa.Text(), nullable=False),
        sa.Column("forecast_summary", sa.Text(), nullable=False),
        sa.Column("failure_type", sa.String(length=96), nullable=True),
        sa.Column("attempted_rule_state", sa.String(length=32), nullable=True),
        sa.Column("attempted_action", sa.String(length=32), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["record_id"], ["signal_review_records.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signal_llm_reviews_failure_type", "signal_llm_reviews", ["failure_type"])


def downgrade() -> None:
    op.drop_index("ix_signal_llm_reviews_failure_type", table_name="signal_llm_reviews")
    op.drop_table("signal_llm_reviews")
    op.drop_index("ix_signal_review_events_manual_status", table_name="signal_review_events")
    op.drop_table("signal_review_events")
    op.drop_index("ix_signal_review_records_ts_code", table_name="signal_review_records")
    op.drop_index("ix_signal_review_records_manual_status", table_name="signal_review_records")
    op.drop_table("signal_review_records")
