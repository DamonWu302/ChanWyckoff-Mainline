from collections.abc import Iterator
from datetime import date, datetime, timedelta, timezone
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
    IntradayBarPayload,
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


def test_backtest_summary_endpoint_runs_date_range_and_parameter_grid() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/backtests/summary",
        json={
            "start": "2026-05-25T10:00:00+00:00",
            "end": "2026-05-27T10:00:00+00:00",
            "parameter_sets": [
                {"name": "fast", "max_holding_bars": 1},
                {"name": "patient", "max_holding_bars": 8},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["start"] == "2026-05-25T10:00:00+00:00"
    assert body["end"] == "2026-05-27T10:00:00+00:00"
    assert body["best"]["name"] == "fast"
    assert body["results"][0]["name"] == "fast"
    assert body["results"][0]["total_trades"] == 2
    assert body["results"][0]["by_signal_state"]["confirmed_3buy"]["total_trades"] == 1
    assert body["results"][0]["by_wyckoff_bucket"]["80-100"]["total_trades"] == 1
    assert "small_sample" in body["results"][0]["risk_flags"]
    assert body["reliability_note"] == "theme_history_reliability_requires_point_in_time_constituents"


def test_backtest_summary_endpoint_uses_ingested_market_data_when_available(
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
    _seed_future_backtest_bars(service, trade_date)
    db_session.commit()

    response = client.post(
        "/api/backtests/summary",
        json={
            "start": "2026-05-29T09:30:00",
            "end": "2026-05-29T17:00:00",
            "parameter_sets": [
                {"name": "fast", "max_holding_bars": 1},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["best"]["name"] == "fast"
    assert body["results"][0]["total_trades"] == 1
    assert body["results"][0]["mean_return"] == "0.022433"
    assert body["results"][0]["by_signal_state"]["confirmed_3buy"]["total_trades"] == 1
    assert body["results"][0]["by_wyckoff_bucket"]["80-100"]["total_trades"] == 1
    assert body["results"][0]["symbol_concentration"] == {"600001.SH": "1"}


def _seed_future_backtest_bars(service: MarketDataIngestionService, trade_date: date) -> None:
    start_time = datetime.combine(trade_date, datetime.min.time(), tzinfo=timezone.utc).replace(hour=9, minute=30)
    service.upsert_intraday_bars(
        [
            IntradayBarPayload(
                ts_code="600001.SH",
                bar_time=start_time + timedelta(minutes=30 * 13),
                frequency="30m",
                adjustment="qfq",
                open=Decimal("10.90"),
                high=Decimal("11.05"),
                low=Decimal("10.84"),
                close=Decimal("11.00"),
                volume=1000000,
                amount=Decimal("11000000.00"),
                source="tickflow",
            ),
            IntradayBarPayload(
                ts_code="600001.SH",
                bar_time=start_time + timedelta(minutes=30 * 14),
                frequency="30m",
                adjustment="qfq",
                open=Decimal("11.00"),
                high=Decimal("11.30"),
                low=Decimal("10.92"),
                close=Decimal("11.30"),
                volume=1100000,
                amount=Decimal("12562000.00"),
                source="tickflow",
            ),
        ]
    )
