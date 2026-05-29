from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.ingestion.market_data import (
    DailyBarPayload,
    InstrumentPayload,
    MarketDataIngestionService,
    ThemeConstituentPayload,
    ThemePayload,
)
from app.main import create_app
from tests.test_dashboard_db_snapshot import (
    _seed_confirmed_3buy_intraday_bars,
    _seed_index_history,
    _seed_theme_history,
)


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


def test_signal_detail_endpoint_returns_structure_price_and_risk_evidence() -> None:
    client = TestClient(create_app())

    response = client.get("/api/signals/600001.SH/detail")

    assert response.status_code == 200
    body = response.json()
    assert body["ts_code"] == "600001.SH"
    assert body["state"] == "confirmed_3buy"
    assert body["suggested_action"] == "upgrade_position"
    assert body["structure"]["label"] == "statistical_platform"
    assert body["structure"]["upper"] == "10.6000"
    assert body["structure"]["lower"] == "9.8000"
    assert body["price_volume"]["breakout_volume_ratio"] == "1.85"
    assert body["wyckoff"]["forecast"] == "continuation_expected"
    assert body["risk"]["position_pct"] == 25
    assert body["risk"]["stop_loss"] == "9.8000"
    assert body["risk"]["invalidations"] == [
        "close_back_inside_structure",
        "heavy_volume_supply_return",
        "pullback_timeout",
    ]


def test_signal_detail_endpoint_returns_404_for_unknown_symbol() -> None:
    client = TestClient(create_app())

    response = client.get("/api/signals/000000.SH/detail")

    assert response.status_code == 404


def test_signal_detail_endpoint_builds_detail_from_ingested_market_data(
    client: TestClient,
    db_session: Session,
) -> None:
    trade_date = date(2026, 5, 29)
    service = MarketDataIngestionService(db_session)
    _seed_index_history(service, trade_date)
    service.upsert_instruments(
        [
            InstrumentPayload(
                symbol="600001",
                exchange="SH",
                name="机器人实盘核心",
                market_board="main_board",
                is_active=True,
                is_st=False,
            )
        ]
    )
    service.upsert_daily_bars(
        [
            DailyBarPayload(
                ts_code="600001.SH",
                trade_date=trade_date,
                adjustment="qfq",
                open=Decimal("10.00"),
                high=Decimal("12.00"),
                low=Decimal("9.80"),
                close=Decimal("11.80"),
                volume=3000000,
                amount=Decimal("360000000.00"),
                turnover_rate=Decimal("5.50"),
                market_cap=Decimal("80000000000.00"),
                source="tickflow",
            )
        ]
    )
    service.upsert_themes(
        [
            ThemePayload(
                source="akshare",
                theme_code="BK9001",
                theme_name="机器人实盘",
                theme_type="concept",
                is_active=True,
            )
        ]
    )
    service.upsert_theme_constituents(
        [
            ThemeConstituentPayload(
                theme_source="akshare",
                theme_code="BK9001",
                ts_code="600001.SH",
                effective_date=trade_date,
                weight=Decimal("0.95"),
                reason="趋势容量核心",
                is_primary=True,
            )
        ]
    )
    _seed_theme_history(service, trade_date)
    _seed_confirmed_3buy_intraday_bars(service, trade_date)
    db_session.commit()

    response = client.get("/api/signals/600001.SH/detail?trade_date=2026-05-29")

    assert response.status_code == 200
    body = response.json()
    assert body["ts_code"] == "600001.SH"
    assert body["name"] == "机器人实盘核心"
    assert body["theme"] == "机器人实盘"
    assert body["state"] == "confirmed_3buy"
    assert body["suggested_action"] == "upgrade_position"
    assert body["structure"]["label"] == "statistical_platform"
    assert body["structure"]["upper"] == "10.6200"
    assert body["structure"]["lower"] == "9.8000"
    assert body["price_volume"]["breakout_volume_ratio"] == "2.00"
    assert body["price_volume"]["pullback_volume"] == "shrinking"
    assert body["wyckoff"]["forecast"] == "continuation_expected"
    assert body["risk"]["stop_loss"] == "9.8000"
