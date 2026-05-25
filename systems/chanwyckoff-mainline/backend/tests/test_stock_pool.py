from collections.abc import Iterator
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.ingestion.market_data import DailyBarPayload, InstrumentPayload, MarketDataIngestionService
from app.selection.stock_pool import StockPoolCriteria, StockPoolService


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with SessionLocal() as session:
        yield session


def seed_stock(
    service: MarketDataIngestionService,
    symbol: str,
    *,
    board: str = "main_board",
    is_active: bool = True,
    is_st: bool = False,
    amount: Decimal = Decimal("600000000"),
    market_cap: Decimal = Decimal("12000000000"),
    turnover_rate: Decimal = Decimal("3.2"),
    close: Decimal = Decimal("10"),
    falling_days: int = 0,
) -> None:
    service.upsert_instruments(
        [
            InstrumentPayload(
                symbol=symbol,
                exchange="SH",
                name=f"测试{symbol}",
                market_board=board,
                is_active=is_active,
                is_st=is_st,
            )
        ]
    )
    trade_date = date(2026, 5, 25)
    bars: list[DailyBarPayload] = []
    for offset in range(6):
        day = trade_date - timedelta(days=5 - offset)
        bar_close = close
        if falling_days and offset >= 6 - falling_days:
            bar_close = close - Decimal(offset - (6 - falling_days) + 1)
        bars.append(
            DailyBarPayload(
                ts_code=f"{symbol}.SH",
                trade_date=day,
                adjustment="qfq",
                open=bar_close,
                high=bar_close + Decimal("0.5"),
                low=bar_close - Decimal("0.5"),
                close=bar_close,
                volume=1000000,
                amount=amount,
                turnover_rate=turnover_rate,
                market_cap=market_cap,
                source="tickflow",
            )
        )
    service.upsert_daily_bars(bars)


def test_tradeable_stock_pool_filters_to_liquid_main_board_candidates(
    db_session: Session,
) -> None:
    ingestion = MarketDataIngestionService(db_session)
    seed_stock(ingestion, "600001")
    seed_stock(ingestion, "600002", is_st=True)
    seed_stock(ingestion, "600003", is_active=False)
    seed_stock(ingestion, "300001", board="gem")
    seed_stock(ingestion, "688001", board="star")
    seed_stock(ingestion, "830001", board="bse")
    seed_stock(ingestion, "600004", amount=Decimal("90000000"))
    seed_stock(ingestion, "600005", market_cap=Decimal("3000000000"))
    seed_stock(ingestion, "600006", turnover_rate=Decimal("0.4"))
    seed_stock(ingestion, "600007", close=Decimal("20"), falling_days=5)

    service = StockPoolService(db_session)
    pool = service.build_tradeable_pool(
        date(2026, 5, 25),
        StockPoolCriteria(
            min_amount=Decimal("200000000"),
            min_market_cap=Decimal("5000000000"),
            min_turnover_rate=Decimal("1.0"),
            max_downtrend_days=4,
        ),
    )

    assert [candidate.ts_code for candidate in pool.candidates] == ["600001.SH"]
    assert pool.excluded["600002.SH"] == "st_or_risk"
    assert pool.excluded["600003.SH"] == "inactive_or_delisted"
    assert pool.excluded["300001.SH"] == "non_main_board"
    assert pool.excluded["688001.SH"] == "non_main_board"
    assert pool.excluded["830001.SH"] == "non_main_board"
    assert pool.excluded["600004.SH"] == "insufficient_amount"
    assert pool.excluded["600005.SH"] == "insufficient_market_cap"
    assert pool.excluded["600006.SH"] == "insufficient_turnover"
    assert pool.excluded["600007.SH"] == "one_way_downtrend"
