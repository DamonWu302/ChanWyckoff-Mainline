from collections.abc import Iterator
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.ingestion.market_data import (
    DailyBarPayload,
    InstrumentPayload,
    IntradayBarPayload,
    MarketDataIngestionService,
    ThemeConstituentPayload,
    ThemePayload,
    ThemeSnapshotPayload,
)


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with SessionLocal() as session:
        yield session


def test_stock_basic_info_import_is_idempotent(db_session: Session) -> None:
    service = MarketDataIngestionService(db_session)

    first_result = service.upsert_instruments(
        [
            InstrumentPayload(
                symbol="600519",
                exchange="SH",
                name="贵州茅台",
                market_board="main_board",
                is_active=True,
                is_st=False,
            )
        ]
    )
    second_result = service.upsert_instruments(
        [
            InstrumentPayload(
                symbol="600519",
                exchange="SH",
                name="贵州茅台A",
                market_board="main_board",
                is_active=True,
                is_st=False,
            )
        ]
    )

    instrument = service.get_instrument("600519.SH")

    assert first_result.created == 1
    assert first_result.updated == 0
    assert second_result.created == 0
    assert second_result.updated == 1
    assert service.count_instruments() == 1
    assert instrument is not None
    assert instrument.name == "贵州茅台A"


def test_qfq_daily_bars_import_is_idempotent(db_session: Session) -> None:
    service = MarketDataIngestionService(db_session)
    service.upsert_instruments(
        [
            InstrumentPayload(
                symbol="600519",
                exchange="SH",
                name="贵州茅台",
                market_board="main_board",
                is_active=True,
                is_st=False,
            )
        ]
    )

    first_result = service.upsert_daily_bars(
        [
            DailyBarPayload(
                ts_code="600519.SH",
                trade_date=date(2026, 5, 25),
                adjustment="qfq",
                open=Decimal("1598.00"),
                high=Decimal("1620.00"),
                low=Decimal("1588.00"),
                close=Decimal("1610.00"),
                volume=12345678,
                amount=Decimal("1987654321.00"),
                source="tickflow",
            )
        ]
    )
    second_result = service.upsert_daily_bars(
        [
            DailyBarPayload(
                ts_code="600519.SH",
                trade_date=date(2026, 5, 25),
                adjustment="qfq",
                open=Decimal("1598.00"),
                high=Decimal("1622.00"),
                low=Decimal("1588.00"),
                close=Decimal("1618.00"),
                volume=12345678,
                amount=Decimal("1987654321.00"),
                source="tickflow",
            )
        ]
    )

    daily_bar = service.get_daily_bar("600519.SH", date(2026, 5, 25), "qfq")

    assert first_result.created == 1
    assert first_result.updated == 0
    assert second_result.created == 0
    assert second_result.updated == 1
    assert service.count_daily_bars() == 1
    assert daily_bar is not None
    assert daily_bar.close == Decimal("1618.0000")


def test_30m_bars_import_is_idempotent(db_session: Session) -> None:
    service = MarketDataIngestionService(db_session)
    service.upsert_instruments(
        [
            InstrumentPayload(
                symbol="600519",
                exchange="SH",
                name="贵州茅台",
                market_board="main_board",
                is_active=True,
                is_st=False,
            )
        ]
    )

    bar_time = datetime(2026, 5, 25, 10, 0, tzinfo=timezone.utc)
    first_result = service.upsert_intraday_bars(
        [
            IntradayBarPayload(
                ts_code="600519.SH",
                bar_time=bar_time,
                frequency="30m",
                adjustment="qfq",
                open=Decimal("1601.00"),
                high=Decimal("1608.00"),
                low=Decimal("1599.00"),
                close=Decimal("1605.00"),
                volume=123400,
                amount=Decimal("19876543.21"),
                source="tickflow",
            )
        ]
    )
    second_result = service.upsert_intraday_bars(
        [
            IntradayBarPayload(
                ts_code="600519.SH",
                bar_time=bar_time,
                frequency="30m",
                adjustment="qfq",
                open=Decimal("1601.00"),
                high=Decimal("1611.00"),
                low=Decimal("1599.00"),
                close=Decimal("1610.00"),
                volume=223400,
                amount=Decimal("29876543.21"),
                source="tickflow",
            )
        ]
    )

    intraday_bar = service.get_intraday_bar("600519.SH", bar_time, "30m", "qfq")

    assert first_result.created == 1
    assert first_result.updated == 0
    assert second_result.created == 0
    assert second_result.updated == 1
    assert service.count_intraday_bars() == 1
    assert intraday_bar is not None
    assert intraday_bar.close == Decimal("1610.0000")


def test_theme_and_constituents_import_is_idempotent(db_session: Session) -> None:
    service = MarketDataIngestionService(db_session)
    service.upsert_instruments(
        [
            InstrumentPayload(
                symbol="600519",
                exchange="SH",
                name="贵州茅台",
                market_board="main_board",
                is_active=True,
                is_st=False,
            )
        ]
    )

    first_theme_result = service.upsert_themes(
        [
            ThemePayload(
                source="eastmoney",
                theme_code="BK1234",
                theme_name="白酒概念",
                theme_type="concept",
                is_active=True,
            )
        ]
    )
    second_theme_result = service.upsert_themes(
        [
            ThemePayload(
                source="eastmoney",
                theme_code="BK1234",
                theme_name="白酒主线",
                theme_type="concept",
                is_active=True,
            )
        ]
    )
    first_constituent_result = service.upsert_theme_constituents(
        [
            ThemeConstituentPayload(
                theme_source="eastmoney",
                theme_code="BK1234",
                ts_code="600519.SH",
                effective_date=date(2026, 5, 25),
                weight=Decimal("0.88"),
                reason="成交额核心",
                is_primary=True,
            )
        ]
    )
    second_constituent_result = service.upsert_theme_constituents(
        [
            ThemeConstituentPayload(
                theme_source="eastmoney",
                theme_code="BK1234",
                ts_code="600519.SH",
                effective_date=date(2026, 5, 25),
                weight=Decimal("0.92"),
                reason="趋势容量核心",
                is_primary=True,
            )
        ]
    )

    theme = service.get_theme("eastmoney", "BK1234")
    constituent = service.get_theme_constituent("eastmoney", "BK1234", "600519.SH", date(2026, 5, 25))

    assert first_theme_result.created == 1
    assert first_theme_result.updated == 0
    assert second_theme_result.created == 0
    assert second_theme_result.updated == 1
    assert service.count_themes() == 1
    assert theme is not None
    assert theme.theme_name == "白酒主线"
    assert first_constituent_result.created == 1
    assert first_constituent_result.updated == 0
    assert second_constituent_result.created == 0
    assert second_constituent_result.updated == 1
    assert service.count_theme_constituents() == 1
    assert constituent is not None
    assert constituent.weight == Decimal("0.920000")
    assert constituent.reason == "趋势容量核心"


def test_theme_snapshots_import_is_idempotent(db_session: Session) -> None:
    service = MarketDataIngestionService(db_session)
    service.upsert_themes(
        [
            ThemePayload(
                source="eastmoney",
                theme_code="BK1234",
                theme_name="白酒概念",
                theme_type="concept",
                is_active=True,
            )
        ]
    )

    first_result = service.upsert_theme_snapshots(
        [
            ThemeSnapshotPayload(
                theme_source="eastmoney",
                theme_code="BK1234",
                trade_date=date(2026, 5, 25),
                close=Decimal("1024.12"),
                pct_change=Decimal("2.34"),
                amount=Decimal("8765432100.00"),
                rising_count=38,
                limit_up_count=3,
                new_high_count=7,
                source="akshare",
            )
        ]
    )
    second_result = service.upsert_theme_snapshots(
        [
            ThemeSnapshotPayload(
                theme_source="eastmoney",
                theme_code="BK1234",
                trade_date=date(2026, 5, 25),
                close=Decimal("1028.12"),
                pct_change=Decimal("2.74"),
                amount=Decimal("9765432100.00"),
                rising_count=40,
                limit_up_count=4,
                new_high_count=8,
                source="akshare",
            )
        ]
    )

    snapshot = service.get_theme_snapshot("eastmoney", "BK1234", date(2026, 5, 25))

    assert first_result.created == 1
    assert first_result.updated == 0
    assert second_result.created == 0
    assert second_result.updated == 1
    assert service.count_theme_snapshots() == 1
    assert snapshot is not None
    assert snapshot.amount == Decimal("9765432100.0000")
    assert snapshot.limit_up_count == 4
