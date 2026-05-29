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
    IndexBarPayload,
    InstrumentPayload,
    IntradayBarPayload,
    MarketDataIngestionService,
    ThemeConstituentPayload,
    ThemePayload,
    ThemeSnapshotPayload,
)
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


def test_dashboard_endpoint_builds_mainline_snapshot_from_ingested_market_data(
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
            ),
            InstrumentPayload(
                symbol="600002",
                exchange="SH",
                name="机器人后排",
                market_board="main_board",
                is_active=True,
                is_st=False,
            ),
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
            ),
            DailyBarPayload(
                ts_code="600002.SH",
                trade_date=trade_date,
                adjustment="qfq",
                open=Decimal("6.00"),
                high=Decimal("6.40"),
                low=Decimal("5.90"),
                close=Decimal("6.20"),
                volume=1800000,
                amount=Decimal("111600000.00"),
                turnover_rate=Decimal("3.20"),
                market_cap=Decimal("18000000000.00"),
                source="tickflow",
            ),
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
            ),
            ThemeConstituentPayload(
                theme_source="akshare",
                theme_code="BK9001",
                ts_code="600002.SH",
                effective_date=trade_date,
                weight=Decimal("0.30"),
                reason="后排跟随",
                is_primary=False,
            ),
        ]
    )
    _seed_theme_history(service, trade_date)
    _seed_confirmed_3buy_intraday_bars(service, trade_date)
    _seed_failed_3buy_intraday_bars(service, trade_date)
    db_session.commit()

    response = client.get("/api/dashboard?trade_date=2026-05-29")
    market_response = client.get("/api/market-regime?trade_date=2026-05-29")
    themes_response = client.get("/api/themes/mainlines?trade_date=2026-05-29")
    signals_response = client.get("/api/signals?trade_date=2026-05-29")

    assert response.status_code == 200
    assert market_response.status_code == 200
    assert themes_response.status_code == 200
    assert signals_response.status_code == 200
    body = response.json()
    market = market_response.json()
    themes = themes_response.json()
    signals = signals_response.json()
    assert body["trade_date"] == "2026-05-29"
    assert body["market_regime"]["state"] == "risk_on"
    assert market["state"] == "risk_on"
    assert body["mainlines"][0]["theme"] == "机器人实盘"
    assert themes[0]["theme"] == "机器人实盘"
    assert body["mainlines"][0]["core_stocks"][0]["ts_code"] == "600001.SH"
    assert body["mainlines"][0]["core_stocks"][0]["name"] == "机器人实盘核心"
    assert body["signals"][0]["ts_code"] == "600001.SH"
    assert body["signals"][0]["name"] == "机器人实盘核心"
    assert body["signals"][0]["theme"] == "机器人实盘"
    assert body["signals"][0]["state"] == "confirmed_3buy"
    assert body["signals"][0]["suggested_action"] == "upgrade_position"
    assert body["signals"][0]["evidence"]["structure"] == "statistical_platform_upper_breakout"
    assert body["signals"][0]["evidence"]["volume_price"] == "pullback_shrinking_accepted"
    failed_signal = next(signal for signal in body["signals"] if signal["ts_code"] == "600002.SH")
    assert failed_signal["state"] == "failed_3buy"
    assert failed_signal["suggested_action"] == "filter"
    assert failed_signal["evidence"]["volume_price"] == "breakout_failed"
    assert signals[0]["ts_code"] == "600001.SH"
    assert signals[0]["state"] == "confirmed_3buy"
    assert {signal["ts_code"] for signal in signals} == {"600001.SH", "600002.SH"}
    assert "机器人核心 Alpha" not in {
        stock["name"]
        for mainline in body["mainlines"]
        for stock in mainline["core_stocks"]
    }


def _seed_index_history(service: MarketDataIngestionService, trade_date: date) -> None:
    for index_code, index_name in [("000001.SH", "上证指数"), ("000985.CSI", "全A指数")]:
        for offset in range(20, -1, -1):
            item_date = trade_date - timedelta(days=offset)
            close = Decimal("3000") + Decimal(20 - offset) * Decimal("5")
            service.upsert_index_bars(
                [
                    IndexBarPayload(
                        index_code=index_code,
                        index_name=index_name,
                        trade_date=item_date,
                        adjustment="none",
                        open=close - Decimal("3"),
                        high=close + Decimal("8"),
                        low=close - Decimal("6"),
                        close=close,
                        volume=100000000 + offset,
                        amount=Decimal("100000000000.00") + Decimal(20 - offset) * Decimal("3000000000.00"),
                        source="tickflow",
                    )
                ]
            )


def _seed_theme_history(service: MarketDataIngestionService, trade_date: date) -> None:
    for offset in range(20, -1, -1):
        amount = Decimal("1000000000.00") if offset else Decimal("2500000000.00")
        service.upsert_theme_snapshots(
            [
                ThemeSnapshotPayload(
                    theme_source="akshare",
                    theme_code="BK9001",
                    trade_date=trade_date - timedelta(days=offset),
                    close=Decimal("1000") + Decimal(20 - offset) * Decimal("12"),
                    pct_change=Decimal("2.8") if offset == 0 else Decimal("0.4"),
                    amount=amount,
                    rising_count=42 if offset == 0 else 18,
                    limit_up_count=7 if offset == 0 else 1,
                    new_high_count=9 if offset == 0 else 1,
                    source="akshare",
                )
            ]
        )


def _seed_confirmed_3buy_intraday_bars(
    service: MarketDataIngestionService,
    trade_date: date,
) -> None:
    start_time = datetime.combine(trade_date, datetime.min.time(), tzinfo=timezone.utc).replace(hour=9, minute=30)
    platform = [
        ("10.30", "9.80", "10.00", 100000),
        ("10.50", "9.90", "10.20", 110000),
        ("10.40", "9.85", "10.05", 105000),
        ("10.55", "9.95", "10.30", 115000),
        ("10.45", "9.90", "10.10", 108000),
        ("10.60", "10.00", "10.35", 112000),
        ("10.50", "9.92", "10.15", 106000),
        ("10.58", "10.02", "10.40", 118000),
        ("10.52", "9.98", "10.25", 109000),
        ("10.62", "10.05", "10.45", 116000),
    ]
    payloads: list[IntradayBarPayload] = []
    for index, (high, low, close, volume) in enumerate(platform):
        payloads.append(
            IntradayBarPayload(
                ts_code="600001.SH",
                bar_time=start_time + timedelta(minutes=30 * index),
                frequency="30m",
                adjustment="qfq",
                open=Decimal(close),
                high=Decimal(high),
                low=Decimal(low),
                close=Decimal(close),
                volume=volume,
                amount=Decimal(volume) * Decimal(close),
                source="tickflow",
            )
        )
    payloads.append(
        IntradayBarPayload(
            ts_code="600001.SH",
            bar_time=start_time + timedelta(minutes=30 * len(platform)),
            frequency="30m",
            adjustment="qfq",
            open=Decimal("10.55"),
            high=Decimal("11.20"),
            low=Decimal("10.50"),
            close=Decimal("10.95"),
            volume=220000,
            amount=Decimal("2409000.00"),
            source="tickflow",
        )
    )
    for offset, (low, close, volume) in enumerate(
        [("10.55", "10.70", 82000), ("10.48", "10.68", 76000)],
        start=1,
    ):
        payloads.append(
            IntradayBarPayload(
                ts_code="600001.SH",
                bar_time=start_time + timedelta(minutes=30 * (len(platform) + offset)),
                frequency="30m",
                adjustment="qfq",
                open=Decimal("10.72"),
                high=Decimal("10.88"),
                low=Decimal(low),
                close=Decimal(close),
                volume=volume,
                amount=Decimal(volume) * Decimal(close),
                source="tickflow",
            )
        )
    service.upsert_intraday_bars(payloads)


def _seed_failed_3buy_intraday_bars(
    service: MarketDataIngestionService,
    trade_date: date,
) -> None:
    start_time = datetime.combine(trade_date, datetime.min.time(), tzinfo=timezone.utc).replace(hour=9, minute=30)
    platform = [
        ("10.30", "9.80", "10.00", 100000),
        ("10.50", "9.90", "10.20", 110000),
        ("10.40", "9.85", "10.05", 105000),
        ("10.55", "9.95", "10.30", 115000),
        ("10.45", "9.90", "10.10", 108000),
        ("10.60", "10.00", "10.35", 112000),
        ("10.50", "9.92", "10.15", 106000),
        ("10.58", "10.02", "10.40", 118000),
        ("10.52", "9.98", "10.25", 109000),
        ("10.62", "10.05", "10.45", 116000),
    ]
    payloads: list[IntradayBarPayload] = []
    for index, (high, low, close, volume) in enumerate(platform):
        payloads.append(
            IntradayBarPayload(
                ts_code="600002.SH",
                bar_time=start_time + timedelta(minutes=30 * index),
                frequency="30m",
                adjustment="qfq",
                open=Decimal(close),
                high=Decimal(high),
                low=Decimal(low),
                close=Decimal(close),
                volume=volume,
                amount=Decimal(volume) * Decimal(close),
                source="tickflow",
            )
        )
    payloads.extend(
        [
            IntradayBarPayload(
                ts_code="600002.SH",
                bar_time=start_time + timedelta(minutes=30 * len(platform)),
                frequency="30m",
                adjustment="qfq",
                open=Decimal("10.55"),
                high=Decimal("11.20"),
                low=Decimal("10.50"),
                close=Decimal("10.95"),
                volume=220000,
                amount=Decimal("2409000.00"),
                source="tickflow",
            ),
            IntradayBarPayload(
                ts_code="600002.SH",
                bar_time=start_time + timedelta(minutes=30 * (len(platform) + 1)),
                frequency="30m",
                adjustment="qfq",
                open=Decimal("10.70"),
                high=Decimal("10.76"),
                low=Decimal("10.05"),
                close=Decimal("10.18"),
                volume=160000,
                amount=Decimal("1628800.00"),
                source="tickflow",
            ),
        ]
    )
    service.upsert_intraday_bars(payloads)
