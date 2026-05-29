from collections.abc import Iterator
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.ingestion.market_bars_pipeline import MarketBarsIngestionPipeline
from app.ingestion.market_data import MarketDataIngestionService
from app.ingestion.providers import MarketBarsDataset


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with SessionLocal() as session:
        yield session


class FakeTickFlowProvider:
    source = "tickflow"

    def fetch_bars(
        self,
        ts_code: str,
        start_date: date,
        end_date: date,
        adjustment: str,
        include_30m: bool,
    ) -> MarketBarsDataset:
        assert ts_code == "600519.SH"
        assert start_date == date(2026, 5, 25)
        assert end_date == date(2026, 5, 25)
        assert adjustment == "qfq"
        assert include_30m is True
        return MarketBarsDataset(
            instruments=[
                {
                    "symbol": "600519",
                    "exchange": "SH",
                    "name": "贵州茅台",
                    "market_board": "main_board",
                    "is_active": True,
                    "is_st": False,
                }
            ],
            daily_bars=[
                {
                    "ts_code": "600519.SH",
                    "trade_date": date(2026, 5, 25),
                    "adjustment": "qfq",
                    "open": Decimal("1598.00"),
                    "high": Decimal("1620.00"),
                    "low": Decimal("1588.00"),
                    "close": Decimal("1610.00"),
                    "volume": 12345678,
                    "amount": Decimal("1987654321.00"),
                    "source": "tickflow",
                }
            ],
            intraday_bars=[
                {
                    "ts_code": "600519.SH",
                    "bar_time": datetime(2026, 5, 25, 10, 0, tzinfo=timezone.utc),
                    "frequency": "30m",
                    "adjustment": "qfq",
                    "open": Decimal("1601.00"),
                    "high": Decimal("1608.00"),
                    "low": Decimal("1599.00"),
                    "close": Decimal("1605.00"),
                    "volume": 123400,
                    "amount": Decimal("19876543.21"),
                    "source": "tickflow",
                }
            ],
        )


class FakeBatchTickFlowProvider:
    source = "tickflow"

    def __init__(self) -> None:
        self.requests: list[tuple[str, date, date, str, bool]] = []

    def fetch_bars(
        self,
        ts_code: str,
        start_date: date,
        end_date: date,
        adjustment: str,
        include_30m: bool,
    ) -> MarketBarsDataset:
        self.requests.append((ts_code, start_date, end_date, adjustment, include_30m))
        symbol, exchange = ts_code.split(".")
        return MarketBarsDataset(
            instruments=[
                {
                    "symbol": symbol,
                    "exchange": exchange,
                    "name": f"测试{symbol}",
                    "market_board": "main_board",
                    "is_active": True,
                    "is_st": False,
                }
            ],
            daily_bars=[
                {
                    "ts_code": ts_code,
                    "trade_date": start_date,
                    "adjustment": adjustment,
                    "open": Decimal("10.00"),
                    "high": Decimal("11.00"),
                    "low": Decimal("9.80"),
                    "close": Decimal("10.50"),
                    "volume": 1000000,
                    "amount": Decimal("10500000.00"),
                    "source": "tickflow",
                }
            ],
            intraday_bars=[
                {
                    "ts_code": ts_code,
                    "bar_time": datetime(2026, 5, 25, 10, 0, tzinfo=timezone.utc),
                    "frequency": "30m",
                    "adjustment": adjustment,
                    "open": Decimal("10.10"),
                    "high": Decimal("10.40"),
                    "low": Decimal("10.00"),
                    "close": Decimal("10.30"),
                    "volume": 100000,
                    "amount": Decimal("1030000.00"),
                    "source": "tickflow",
                }
            ],
        )


def test_market_bars_pipeline_imports_tickflow_dataset_idempotently(db_session: Session) -> None:
    service = MarketDataIngestionService(db_session)
    pipeline = MarketBarsIngestionPipeline(service, FakeTickFlowProvider())

    first_result = pipeline.import_bars(
        "600519.SH",
        date(2026, 5, 25),
        date(2026, 5, 25),
        adjustment="qfq",
        include_30m=True,
    )
    second_result = pipeline.import_bars(
        "600519.SH",
        date(2026, 5, 25),
        date(2026, 5, 25),
        adjustment="qfq",
        include_30m=True,
    )

    assert first_result.instruments.created == 1
    assert first_result.daily_bars.created == 1
    assert first_result.intraday_bars.created == 1
    assert second_result.instruments.updated == 1
    assert second_result.daily_bars.updated == 1
    assert second_result.intraday_bars.updated == 1
    assert service.count_instruments() == 1
    assert service.count_daily_bars() == 1
    assert service.count_intraday_bars() == 1


def test_market_bars_pipeline_imports_symbol_batch(db_session: Session) -> None:
    service = MarketDataIngestionService(db_session)
    provider = FakeBatchTickFlowProvider()
    pipeline = MarketBarsIngestionPipeline(service, provider)

    result = pipeline.import_symbol_batch(
        ["600001.SH", "000001.SZ"],
        date(2026, 5, 25),
        date(2026, 5, 26),
        adjustment="qfq",
        include_30m=True,
    )

    assert provider.requests == [
        ("600001.SH", date(2026, 5, 25), date(2026, 5, 26), "qfq", True),
        ("000001.SZ", date(2026, 5, 25), date(2026, 5, 26), "qfq", True),
    ]
    assert result.instruments.created == 2
    assert result.daily_bars.created == 2
    assert result.intraday_bars.created == 2
    assert service.count_instruments() == 2
    assert service.count_daily_bars() == 2
    assert service.count_intraday_bars() == 2
