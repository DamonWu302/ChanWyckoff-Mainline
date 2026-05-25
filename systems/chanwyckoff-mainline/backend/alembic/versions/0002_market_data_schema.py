"""market data schema

Revision ID: 0002_market_data_schema
Revises: 0001_initial_schema
Create Date: 2026-05-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_market_data_schema"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "instruments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ts_code", sa.String(length=16), nullable=False),
        sa.Column("symbol", sa.String(length=12), nullable=False),
        sa.Column("exchange", sa.String(length=8), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("market_board", sa.String(length=32), nullable=False),
        sa.Column("industry", sa.String(length=64), nullable=True),
        sa.Column("list_date", sa.Date(), nullable=True),
        sa.Column("delist_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_st", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", "exchange", name="uq_instruments_symbol_exchange"),
        sa.UniqueConstraint("ts_code"),
    )
    op.create_index("ix_instruments_is_active", "instruments", ["is_active"])
    op.create_index("ix_instruments_market_board", "instruments", ["market_board"])

    op.create_table(
        "trading_calendars",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("exchange", sa.String(length=8), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("is_open", sa.Boolean(), nullable=False),
        sa.Column("previous_trade_date", sa.Date(), nullable=True),
        sa.Column("next_trade_date", sa.Date(), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exchange", "trade_date", name="uq_calendar_exchange_date"),
    )

    op.create_table(
        "themes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("theme_code", sa.String(length=64), nullable=False),
        sa.Column("theme_name", sa.String(length=128), nullable=False),
        sa.Column("theme_type", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "theme_code", name="uq_themes_source_code"),
    )

    op.create_table(
        "index_bars",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("index_code", sa.String(length=32), nullable=False),
        sa.Column("index_name", sa.String(length=64), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("adjustment", sa.String(length=16), nullable=False),
        sa.Column("open", sa.Numeric(18, 4), nullable=False),
        sa.Column("high", sa.Numeric(18, 4), nullable=False),
        sa.Column("low", sa.Numeric(18, 4), nullable=False),
        sa.Column("close", sa.Numeric(18, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("amount", sa.Numeric(24, 4), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("index_code", "trade_date", "adjustment", name="uq_index_bar"),
    )
    op.create_index("ix_index_bars_trade_date", "index_bars", ["trade_date"])

    op.create_table(
        "daily_bars",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("adjustment", sa.String(length=16), nullable=False),
        sa.Column("open", sa.Numeric(18, 4), nullable=False),
        sa.Column("high", sa.Numeric(18, 4), nullable=False),
        sa.Column("low", sa.Numeric(18, 4), nullable=False),
        sa.Column("close", sa.Numeric(18, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Numeric(24, 4), nullable=False),
        sa.Column("turnover_rate", sa.Numeric(12, 6), nullable=True),
        sa.Column("market_cap", sa.Numeric(24, 4), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instrument_id", "trade_date", "adjustment", name="uq_daily_bar"),
    )
    op.create_index("ix_daily_bars_trade_date", "daily_bars", ["trade_date"])

    op.create_table(
        "intraday_bars",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("bar_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("frequency", sa.String(length=16), nullable=False),
        sa.Column("adjustment", sa.String(length=16), nullable=False),
        sa.Column("open", sa.Numeric(18, 4), nullable=False),
        sa.Column("high", sa.Numeric(18, 4), nullable=False),
        sa.Column("low", sa.Numeric(18, 4), nullable=False),
        sa.Column("close", sa.Numeric(18, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Numeric(24, 4), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "instrument_id", "bar_time", "frequency", "adjustment", name="uq_intraday_bar"
        ),
    )
    op.create_index("ix_intraday_bars_bar_time", "intraday_bars", ["bar_time"])

    op.create_table(
        "theme_constituents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("theme_id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("weight", sa.Numeric(12, 6), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.ForeignKeyConstraint(["theme_id"], ["themes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("theme_id", "instrument_id", "effective_date", name="uq_theme_constituent"),
    )
    op.create_index(
        "ix_theme_constituents_effective_date", "theme_constituents", ["effective_date"]
    )

    op.create_table(
        "theme_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("theme_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("close", sa.Numeric(18, 4), nullable=True),
        sa.Column("pct_change", sa.Numeric(12, 6), nullable=True),
        sa.Column("amount", sa.Numeric(24, 4), nullable=True),
        sa.Column("rising_count", sa.Integer(), nullable=True),
        sa.Column("limit_up_count", sa.Integer(), nullable=True),
        sa.Column("new_high_count", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["theme_id"], ["themes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("theme_id", "trade_date", name="uq_theme_snapshot"),
    )
    op.create_index("ix_theme_snapshots_trade_date", "theme_snapshots", ["trade_date"])

    op.create_table(
        "tdx_daily_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ts_code", sa.String(length=16), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(24, 4), nullable=True),
        sa.Column("turnover_rate", sa.Numeric(12, 6), nullable=True),
        sa.Column("market_cap", sa.Numeric(24, 4), nullable=True),
        sa.Column("raw_payload", sa.Text(), nullable=True),
        sa.Column("source_file", sa.String(length=255), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ts_code", "trade_date", name="uq_tdx_daily_snapshot"),
    )
    op.create_index("ix_tdx_daily_snapshots_trade_date", "tdx_daily_snapshots", ["trade_date"])

    op.create_table(
        "data_ingestion_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("dataset", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_range_start", sa.Date(), nullable=True),
        sa.Column("requested_range_end", sa.Date(), nullable=True),
        sa.Column("records_read", sa.Integer(), nullable=False),
        sa.Column("records_written", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_ingestion_runs_provider", "data_ingestion_runs", ["provider"])
    op.create_index("ix_data_ingestion_runs_status", "data_ingestion_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_data_ingestion_runs_status", table_name="data_ingestion_runs")
    op.drop_index("ix_data_ingestion_runs_provider", table_name="data_ingestion_runs")
    op.drop_table("data_ingestion_runs")
    op.drop_index("ix_tdx_daily_snapshots_trade_date", table_name="tdx_daily_snapshots")
    op.drop_table("tdx_daily_snapshots")
    op.drop_index("ix_theme_snapshots_trade_date", table_name="theme_snapshots")
    op.drop_table("theme_snapshots")
    op.drop_index("ix_theme_constituents_effective_date", table_name="theme_constituents")
    op.drop_table("theme_constituents")
    op.drop_index("ix_intraday_bars_bar_time", table_name="intraday_bars")
    op.drop_table("intraday_bars")
    op.drop_index("ix_daily_bars_trade_date", table_name="daily_bars")
    op.drop_table("daily_bars")
    op.drop_index("ix_index_bars_trade_date", table_name="index_bars")
    op.drop_table("index_bars")
    op.drop_table("themes")
    op.drop_table("trading_calendars")
    op.drop_index("ix_instruments_market_board", table_name="instruments")
    op.drop_index("ix_instruments_is_active", table_name="instruments")
    op.drop_table("instruments")
