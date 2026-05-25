from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Instrument(TimestampMixin, Base):
    __tablename__ = "instruments"
    __table_args__ = (
        UniqueConstraint("symbol", "exchange", name="uq_instruments_symbol_exchange"),
        Index("ix_instruments_market_board", "market_board"),
        Index("ix_instruments_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    symbol: Mapped[str] = mapped_column(String(12), nullable=False)
    exchange: Mapped[str] = mapped_column(String(8), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    market_board: Mapped[str] = mapped_column(String(32), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(64))
    list_date: Mapped[date | None] = mapped_column(Date)
    delist_date: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_st: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    daily_bars: Mapped[list["DailyBar"]] = relationship(back_populates="instrument")
    intraday_bars: Mapped[list["IntradayBar"]] = relationship(back_populates="instrument")
    theme_links: Mapped[list["ThemeConstituent"]] = relationship(back_populates="instrument")


class TradingCalendar(TimestampMixin, Base):
    __tablename__ = "trading_calendars"
    __table_args__ = (UniqueConstraint("exchange", "trade_date", name="uq_calendar_exchange_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exchange: Mapped[str] = mapped_column(String(8), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False)
    previous_trade_date: Mapped[date | None] = mapped_column(Date)
    next_trade_date: Mapped[date | None] = mapped_column(Date)


class DailyBar(TimestampMixin, Base):
    __tablename__ = "daily_bars"
    __table_args__ = (
        UniqueConstraint("instrument_id", "trade_date", "adjustment", name="uq_daily_bar"),
        Index("ix_daily_bars_trade_date", "trade_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    adjustment: Mapped[str] = mapped_column(String(16), nullable=False, default="qfq")
    open: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    turnover_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    market_cap: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    source: Mapped[str] = mapped_column(String(32), nullable=False)

    instrument: Mapped[Instrument] = relationship(back_populates="daily_bars")


class IntradayBar(TimestampMixin, Base):
    __tablename__ = "intraday_bars"
    __table_args__ = (
        UniqueConstraint("instrument_id", "bar_time", "frequency", "adjustment", name="uq_intraday_bar"),
        Index("ix_intraday_bars_bar_time", "bar_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    bar_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    frequency: Mapped[str] = mapped_column(String(16), nullable=False, default="30m")
    adjustment: Mapped[str] = mapped_column(String(16), nullable=False, default="qfq")
    open: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)

    instrument: Mapped[Instrument] = relationship(back_populates="intraday_bars")


class IndexBar(TimestampMixin, Base):
    __tablename__ = "index_bars"
    __table_args__ = (
        UniqueConstraint("index_code", "trade_date", "adjustment", name="uq_index_bar"),
        Index("ix_index_bars_trade_date", "trade_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    index_code: Mapped[str] = mapped_column(String(32), nullable=False)
    index_name: Mapped[str] = mapped_column(String(64), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    adjustment: Mapped[str] = mapped_column(String(16), nullable=False, default="none")
    open: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    volume: Mapped[int | None] = mapped_column(BigInteger)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    source: Mapped[str] = mapped_column(String(32), nullable=False)


class Theme(TimestampMixin, Base):
    __tablename__ = "themes"
    __table_args__ = (UniqueConstraint("source", "theme_code", name="uq_themes_source_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    theme_code: Mapped[str] = mapped_column(String(64), nullable=False)
    theme_name: Mapped[str] = mapped_column(String(128), nullable=False)
    theme_type: Mapped[str] = mapped_column(String(32), nullable=False, default="concept")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    constituents: Mapped[list["ThemeConstituent"]] = relationship(back_populates="theme")
    snapshots: Mapped[list["ThemeSnapshot"]] = relationship(back_populates="theme")


class ThemeConstituent(TimestampMixin, Base):
    __tablename__ = "theme_constituents"
    __table_args__ = (
        UniqueConstraint("theme_id", "instrument_id", "effective_date", name="uq_theme_constituent"),
        Index("ix_theme_constituents_effective_date", "effective_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    theme_id: Mapped[int] = mapped_column(ForeignKey("themes.id"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    reason: Mapped[str | None] = mapped_column(String(255))
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    theme: Mapped[Theme] = relationship(back_populates="constituents")
    instrument: Mapped[Instrument] = relationship(back_populates="theme_links")


class ThemeSnapshot(TimestampMixin, Base):
    __tablename__ = "theme_snapshots"
    __table_args__ = (
        UniqueConstraint("theme_id", "trade_date", name="uq_theme_snapshot"),
        Index("ix_theme_snapshots_trade_date", "trade_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    theme_id: Mapped[int] = mapped_column(ForeignKey("themes.id"), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    close: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    pct_change: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    rising_count: Mapped[int | None] = mapped_column(Integer)
    limit_up_count: Mapped[int | None] = mapped_column(Integer)
    new_high_count: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(32), nullable=False)

    theme: Mapped[Theme] = relationship(back_populates="snapshots")


class TdxDailySnapshot(TimestampMixin, Base):
    __tablename__ = "tdx_daily_snapshots"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_tdx_daily_snapshot"),
        Index("ix_tdx_daily_snapshots_trade_date", "trade_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    turnover_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    market_cap: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    raw_payload: Mapped[str | None] = mapped_column(Text)
    source_file: Mapped[str | None] = mapped_column(String(255))


class DataIngestionRun(TimestampMixin, Base):
    __tablename__ = "data_ingestion_runs"
    __table_args__ = (
        Index("ix_data_ingestion_runs_provider", "provider"),
        Index("ix_data_ingestion_runs_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    dataset: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    requested_range_start: Mapped[date | None] = mapped_column(Date)
    requested_range_end: Mapped[date | None] = mapped_column(Date)
    records_read: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_written: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
