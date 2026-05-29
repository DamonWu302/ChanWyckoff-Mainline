from collections.abc import Iterator
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.ingestion.market_data import DailyBarPayload, InstrumentPayload, MarketDataIngestionService
from app.main import create_app


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with SessionLocal() as session:
        yield session


@pytest.fixture()
def client(db_session: Session) -> Iterator[TestClient]:
    app = create_app()

    def override_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_stock_pool_endpoint_returns_tradeable_main_board_candidates(
    client: TestClient,
    db_session: Session,
) -> None:
    service = MarketDataIngestionService(db_session)
    _seed_stock(service, "600001", name="主板核心")
    _seed_stock(service, "600002", name="风险警示", is_st=True)
    _seed_stock(service, "300001", name="创业板样本", board="gem")
    _seed_stock(service, "600003", name="低成交额", amount=Decimal("90000000"))
    _seed_stock(service, "600004", name="低市值", market_cap=Decimal("3000000000"))
    _seed_stock(service, "600005", name="低换手", turnover_rate=Decimal("0.4"))

    response = client.get("/api/stock-pool?trade_date=2026-05-29")

    assert response.status_code == 200
    body = response.json()
    assert body["trade_date"] == "2026-05-29"
    assert body["criteria"] == {
        "min_amount": "100000000",
        "min_market_cap": "5000000000",
        "min_turnover_rate": "1.0",
        "max_downtrend_days": 5,
    }
    assert body["candidates"] == [
        {
            "ts_code": "600001.SH",
            "name": "主板核心",
            "amount": "600000000.0000",
            "market_cap": "12000000000.0000",
            "turnover_rate": "3.2000",
        }
    ]
    assert body["excluded"] == {
        "300001.SH": "non_main_board",
        "600002.SH": "st_or_risk",
        "600003.SH": "insufficient_amount",
        "600004.SH": "insufficient_market_cap",
        "600005.SH": "insufficient_turnover",
    }


def _seed_stock(
    service: MarketDataIngestionService,
    symbol: str,
    *,
    name: str,
    board: str = "main_board",
    is_st: bool = False,
    amount: Decimal = Decimal("600000000"),
    market_cap: Decimal = Decimal("12000000000"),
    turnover_rate: Decimal = Decimal("3.2"),
) -> None:
    service.upsert_instruments(
        [
            InstrumentPayload(
                symbol=symbol,
                exchange="SH",
                name=name,
                market_board=board,
                is_active=True,
                is_st=is_st,
            )
        ]
    )
    trade_date = date(2026, 5, 29)
    service.upsert_daily_bars(
        [
            DailyBarPayload(
                ts_code=f"{symbol}.SH",
                trade_date=trade_date - timedelta(days=offset),
                adjustment="qfq",
                open=Decimal("10"),
                high=Decimal("10.5"),
                low=Decimal("9.8"),
                close=Decimal("10.2"),
                volume=1000000,
                amount=amount,
                turnover_rate=turnover_rate,
                market_cap=market_cap,
                source="tickflow",
            )
            for offset in range(3)
        ]
    )
