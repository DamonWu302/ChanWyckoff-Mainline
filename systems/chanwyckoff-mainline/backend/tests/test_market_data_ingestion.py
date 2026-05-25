from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.ingestion.market_data import DailyBarPayload, InstrumentPayload, MarketDataIngestionService


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
