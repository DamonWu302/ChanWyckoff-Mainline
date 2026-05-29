from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.ingestion.index_bars_pipeline import IndexBarsIngestionPipeline
from app.ingestion.market_data import MarketDataIngestionService
from app.ingestion.providers import IndexBarsDataset


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with SessionLocal() as session:
        yield session


class FakeIndexBarsProvider:
    source = "tickflow"

    def __init__(self) -> None:
        self.requests: list[tuple[str, date, date, str]] = []

    def fetch_index_bars(
        self,
        index_code: str,
        start_date: date,
        end_date: date,
        adjustment: str,
    ) -> IndexBarsDataset:
        self.requests.append((index_code, start_date, end_date, adjustment))
        return IndexBarsDataset(
            index_bars=[
                {
                    "index_code": index_code,
                    "index_name": "上证指数",
                    "trade_date": start_date,
                    "adjustment": adjustment,
                    "open": Decimal("3120.10"),
                    "high": Decimal("3160.20"),
                    "low": Decimal("3108.30"),
                    "close": Decimal("3150.40"),
                    "volume": 123456789,
                    "amount": Decimal("456789012345.00"),
                    "source": "tickflow",
                }
            ]
        )


def test_index_bars_pipeline_imports_provider_dataset_idempotently(db_session: Session) -> None:
    service = MarketDataIngestionService(db_session)
    provider = FakeIndexBarsProvider()
    pipeline = IndexBarsIngestionPipeline(service, provider)

    first_result = pipeline.import_index_bars(
        "000001.SH",
        date(2026, 5, 25),
        date(2026, 5, 26),
        adjustment="none",
    )
    second_result = pipeline.import_index_bars(
        "000001.SH",
        date(2026, 5, 25),
        date(2026, 5, 26),
        adjustment="none",
    )

    assert provider.requests == [
        ("000001.SH", date(2026, 5, 25), date(2026, 5, 26), "none"),
        ("000001.SH", date(2026, 5, 25), date(2026, 5, 26), "none"),
    ]
    assert first_result.created == 1
    assert second_result.updated == 1
    assert service.count_index_bars() == 1
