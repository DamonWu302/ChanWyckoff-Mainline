from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.ingestion.market_data import InstrumentPayload, MarketDataIngestionService
from app.ingestion.providers import ThemeProviderDataset
from app.ingestion.theme_pipeline import ThemeIngestionPipeline


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with SessionLocal() as session:
        yield session


class FakeThemeProvider:
    source = "akshare"

    def fetch_trade_date(self, trade_date: date) -> ThemeProviderDataset:
        return ThemeProviderDataset(
            themes=[
                {
                    "source": "eastmoney",
                    "theme_code": "BK1234",
                    "theme_name": "白酒主线",
                    "theme_type": "concept",
                    "is_active": True,
                }
            ],
            constituents=[
                {
                    "theme_source": "eastmoney",
                    "theme_code": "BK1234",
                    "ts_code": "600519.SH",
                    "effective_date": trade_date,
                    "weight": Decimal("0.92"),
                    "reason": "趋势容量核心",
                    "is_primary": True,
                }
            ],
            snapshots=[
                {
                    "theme_source": "eastmoney",
                    "theme_code": "BK1234",
                    "trade_date": trade_date,
                    "close": Decimal("1028.12"),
                    "pct_change": Decimal("2.74"),
                    "amount": Decimal("9765432100.00"),
                    "rising_count": 40,
                    "limit_up_count": 4,
                    "new_high_count": 8,
                    "source": "akshare",
                }
            ],
        )


def test_theme_pipeline_imports_provider_dataset_idempotently(db_session: Session) -> None:
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
    pipeline = ThemeIngestionPipeline(service, FakeThemeProvider())

    first_result = pipeline.import_trade_date(date(2026, 5, 25))
    second_result = pipeline.import_trade_date(date(2026, 5, 25))

    assert first_result.themes.created == 1
    assert first_result.constituents.created == 1
    assert first_result.snapshots.created == 1
    assert second_result.themes.updated == 1
    assert second_result.constituents.updated == 1
    assert second_result.snapshots.updated == 1
    assert service.count_themes() == 1
    assert service.count_theme_constituents() == 1
    assert service.count_theme_snapshots() == 1
